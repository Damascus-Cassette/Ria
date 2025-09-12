''' Entity local and foreign declaration, Foregin is the non-local interface of a connection by declared entity typ '''

import os
import yaml
import asyncio
from fastapi.responses import HTMLResponse
from pathlib import Path
from contextvars import ContextVar

from fastapi        import (Request, Response, APIRouter, WebSocket as WebSocket_Manager)
from sqlalchemy     import (Column, Boolean, ForeignKey, Integer, String, create_engine, Table, Engine as EngineType, Enum as Sql_Enum, )
from sqlalchemy.orm import (declarative_base, relationship, sessionmaker, Mapped, mapped_column ,Session as SessionType)

from .Job_Database_Model            import Base as Job_DB_Model
from ..File_Management              import File_DB_Model
from .Statics                       import Entity_Types, Trust_States, Connection_States
from ..Web_Interface.API_V1_8       import Foreign_Entity_Base, Local_Entity_Base, Interface_Base, IO
from ..Web_Interface.Websocket_Pool import Client_Websocket_Pool,Manager_Websocket_Pool,Manager_Websocket_Wrapper_Base
from .Entity_Settings               import Manager_Settings, Worker_Settings
from .Entity_Settings_Common        import CURRENT_DIR
from ..Struct_Pub_Sub_v1_2          import Event_Router
from ..Pub_Sub_Sql_Events_Factory   import set_listeners_on_tables

from starlette.websockets import WebSocketState as Manager_WebSocketState 
from copy import copy

from typing import Any

Client_DB_Model = declarative_base()

FAPI_SHUTTING_DOWN = ContextVar('FAPI_SHUTTING_DOWN',default = False)

class UNDEC_Foreign(Foreign_Entity_Base,Client_DB_Model):
    '''UNREGISTERED & UNTRUSTED CONNECTION, CLIENTS WILL BE DEFINED ELSEWHERE AND ALWAYS PASS IN UID + SEC KEY'''

    __tablename__ = Entity_Types.UNDEC.value 
    _interactive  = False
    Entity_Type   = Entity_Types.UNDEC

    def __init__(self,host,port):
        self.host = host
        self.port = port
        # self.id  = host + ':' +port

    uid  = Column(Integer, primary_key=True)
    host = Column(String)
    port = Column(String)

    @property
    def unique_id(self):
        return self.id

    def __repr__(self):
        return f'< {self.Entity_Type} | {self.host}:{self.port} @ row {self.id} > '

    def matches_request(self, request:Request, headers:Request.headers):
        return all([
            str(self.host) == str(request.client.host),
        ])

    def intake_request(self, request:Request, headers:Request.headers):
        self.host = request.client.host
        self.port = request.client.port
    
    @classmethod
    def New_From_Request(cls, local_entity, request):
        # raise Exception(f'UNKNOWN:{ra}')
        return cls(request.client.host, request.client.port)

from ..Web_Interface.Websocket_Pool import Manager_Websocket_Wrapper_Simul_Default
from starlette.websockets import WebSocketDisconnect as Manager_WebSocketDisconnect 
    
class Websocket_State_Info(Manager_Websocket_Wrapper_Simul_Default):
    Events = Event_Router.New()
    events = None

    local_entity   : 'Manager_Local'
    foreign_entity : 'UNDEC_Foreign'

    def pre_run(self, buffer_tick_rate = 2):
        self.buffer = []
        self.buffer_tick_rate = buffer_tick_rate
        self.start_populate_buffer()
        if not self.events:
            self.events = self.Events(self)
        self.events_callback = self.local_entity.events.temp_attach_router_inst(self.events)

    def after(self,):
        self.events_callback()
    
    def make_simul_tasks(self,):
        ''' Re-creates tasks on each completion
        TODO: Instead optionally make bellow a factory to re-queue each indv automatically '''
        
        return [
            asyncio.create_task(self.send_buffer()),
            asyncio.create_task(self.receive_json()),
        ]

    async def send_buffer(self):
        while True:
            if len(self.buffer):
                buffer = copy(self.buffer)
                self.buffer.clear()
                for x in buffer:
                    await self.websocket.send_json(x)
            await asyncio.sleep(self.buffer_tick_rate)

    async def receive_json(self):
        val = await self.websocket.receive_json()
        print('Got Val:', val)

    def start_populate_buffer(self,):
        self.buffer.extend([
            ('BULK_CREATE','workers'    , self.gather_intial_send(self.local_entity.client_db_session, Worker_Foreign  , ['id','host','port'] )),
            ('BULK_CREATE','UNDECLARED' , self.gather_intial_send(self.local_entity.client_db_session, UNDEC_Foreign   , ['id','host','port'] )), #|self.gather_all_clients()
            ('BULK_CREATE','managers'   , self.gather_intial_send(self.local_entity.client_db_session, Manager_Foreign , ['id','host','port'] )),
            ('BULK_CREATE','clients'    , self.gather_intial_send(self.local_entity.client_db_session, Client_Foreign  , ['id','host','port'] )), #|self.gather_all_clients()
            # ('BULK_CREATE','jobs',    self.gather_all_jobs( this_e.))
        ])


    def gather_intial_send(self, session, table, attrs):
        res = []
        for row in session.query(table).all():
            res.append(self.gather_item(row,attrs))
        return res

    def gather_item(self,row, attrs):
        item = {}
        for attr in attrs:
            item[attr] = getattr(row, attr, None)
        return item        

    @Events.Sub('after_insert')
    def insert_client(self, event, event_key, container, mapper, connection):
        self.buffer.append(('CREATE', container.__tablename__ , self.gather_item(container,['id','host','port'])))

    @Events.Sub('after_update')
    def update_client(self, event, event_key, container, mapper, connection):
        self.buffer.append(('UPDATE', container.__tablename__ , self.gather_item(container,['id','host','port'])))

    @Events.Sub('after_delete')
    def delete_client(self, event, event_key, container, mapper, connection):
        self.buffer.append(('DELETE', container.__tablename__ , self.gather_item(container,['id','host','port'])))


class Manager_Interface_Info(Interface_Base):
    router = APIRouter()
    @IO.Get(router,'/')
    def base_page(self, this_e, other_e, req, ):
        return this_e.fapi_templates.TemplateResponse(
            "/info/info1.html",
            {   'request' : req, 
                'Manager_Name':this_e.settings.label},
        )
        # return HTMLResponse(content=html_content)
        # return 'HI!'
        ...

    @IO.Websocket(router,'/state-info')
    async def state_info(self, this_e, other_e, websocket:WebSocket_Manager):
        ws = Websocket_State_Info(this_e, other_e, websocket, 'state_info')
        await ws.accept()
        try:
            await ws.run_handler()
        except Manager_WebSocketDisconnect:
            print('REACHED WEBSOCKET DISCON')
            await ws.close()


from ws4py.client.threadedclient import WebSocketClient 

class Manager_Worker_Interface(Interface_Base):
    router = APIRouter()
    
    @IO.Get(router,'/test')
    def test(self, this_e, other_e, req):
        return True

    @IO.Websocket(router,'/ws')
    async def worker_websocket(self, this_e, other_e, websocket:WebSocket_Manager):
        from starlette.websockets import WebSocketDisconnect,WebSocketClose
        await websocket.accept()
        await websocket.send_text('Hello')
        await websocket.close()
    @worker_websocket.Client()
    async def worker_websocket_client(self,this_e:Foreign_Entity_Base, other_e:Local_Entity_Base, path, headers):

        class custom_ws_class(WebSocketClient):
            def opened(self):
                pool = other_e.client_websocket_pool
                pool.attach(other_e, this_e, self,self.__class__.__name__)
                self.send('GREETINGS!')
                # self.close()
                
            def closed(self, code, reason=None):
                pool = other_e.client_websocket_pool
                pool.remove(self)
                print('WEBSOCKET CLOSED!')
            
            def received_message(self, message):
                print('RECEIVED MESSAGE:', message)
                self.send('GOODBYE!')
                self.close()
            
            async def run_forever(self):
                return super().run_forever()

        fullpath = f'ws://{this_e.host}:{this_e.port}' + path
        print(fullpath)

        ws = custom_ws_class(fullpath, headers=headers.items())
        try:
            ws.connect()
            asyncio.create_task(ws.run_forever())
            return ws
        except Exception as e:
            print(f'Cound not connect! Reason: {e}')
            return None

class Worker_Interface(Interface_Base):
    ''' Worker interface is websocket msg : pub-sub based'''
    ...

class Local_Common():

    def export_header(self, to_entity:Foreign_Entity_Base)->dict:
        return {'Role': self.Entity_Type.value, 
                'UID' : self.uid}

    def export_header(self, to_entity:Foreign_Entity_Base)->dict:
        return {'Role': self.Entity_Type.value, 
                'UID' : self.uid}

    async def Find_Entity_From_Req(self, request:Request):
        ''' Ensure DB Connection, return foreign item '''
        if incoming_role:=request.headers.get('role'):
            table = ROLE_TABLE_MAPPING[incoming_role]
            print('GOT ROLE:', incoming_role)
        else:
            table = UNDEC_Foreign
        rows = self.session.query(table).all()
        for row in rows:
            if row.matches_request(request, request.headers):
                row.intake_request(request, request.headers)
                self.session.commit()
                return row
            
        new_row = table.New_From_Request(self,request)
        self.session.add(new_row)
        self.session.commit()
        return new_row

    async def Find_Entity_From_WsReq(self, request:WebSocket_Manager):
        ''' Ensure DB Connection in websocket context, return foreign item '''
        return await self.Find_Entity_From_Req(request)
    
    def load_settings(self,settings_loc):
        ''' Ensure settings exist, from calling directory if relative? '''
        if settings_loc.startswith('.'):
            settings_loc = Path(CURRENT_DIR.get() + settings_loc).resolve()

        
        if not Path(settings_loc).exists():
            settings = self.SettingsType()
            data = settings._export_()
            with open(settings_loc,'w') as f:
                yaml.dump(data,f,sort_keys=False)
            self.settings = settings
        else:        
            with open(settings_loc,'r') as f:
                data = yaml.load(f, yaml.BaseLoader)
                self.settings = self.SettingsType()
                self.settings._import_(data)

        CURRENT_DIR.set(str(self.settings.root_dir))
        #resolves root dir if relative to current path, settins as current dict
        #Must be done before other loading steps.

    @classmethod
    def fapi_app(cls, *args, **kwargs):
        from fastapi import FastAPI
        from fastapi.staticfiles import StaticFiles 


        inst  = cls(*args,**kwargs)
        app = FastAPI(lifespan=inst.fapi_lifespan)

        from fastapi.templating import Jinja2Templates
        static_path = f'{Path(__file__).parents[0]}/Manager_Statics' #HACK, rely on env vars for nuitka unpack  
        inst.fapi_templates = Jinja2Templates(directory=static_path)
        app.mount("/static", StaticFiles(directory=static_path), name="static")

        @app.get("/url-list")
        def get_all_urls():
            url_list = [{"path": route.path, "name": route.name} for route in app.routes]
            return url_list

        return  inst.attach_to_app(app)
    
    async def fapi_lifespan(self,app):
        yield

    # def fapi_mount_static(self,app):
    #     from fastapi import StaticFiles
    #     app.mount("/static", StaticFiles(directory="static"), name="static")
    #     ...

class Manager_Local(Local_Common,Local_Entity_Base):
    Entity_Type         = Entity_Types.MANAGER
    SettingsType        = Manager_Settings
    InterfaceType       = Manager_Interface_Info
    WorkerInterfaceType = Manager_Worker_Interface
    _Fapi_Dep_Path = '/Manager_Statics'


    Events             = Event_Router.New(readout=True)

    interface              : Manager_Interface_Info
    worker_interface       : Manager_Worker_Interface

    settings               : Manager_Settings
    manager_websocket_pool : Manager_Websocket_Pool
    client_websocket_pool  : Client_Websocket_Pool
         
    # services_pool : ServicesPoolType
    # event_handler : EventHandlerType

    File_DB_Engine    : EngineType
    File_DB_Session   : SessionType
    file_db_session   : SessionType

    Job_DB_Engine     : EngineType
    Job_DB_Session    : SessionType
    job_db_session    : SessionType

    Client_DB_Engine  : EngineType
    Client_DB_Session : SessionType
    client_db_session : SessionType
    

    def __init__(self, settings_loc:str='./manger_settings.yaml'):
        self.interface              = self.InterfaceType(self)
        self.worker_interface       = self.WorkerInterfaceType(self)
        self.manager_websocket_pool = Manager_Websocket_Pool()
        self.client_websocket_pool  = Client_Websocket_Pool()
        self.events = self.Events(self)
        
        self.load_settings(settings_loc)
        #self.services_pool = ServicesPoolType(self)
        #self.event_handler = EventHandlerType(self)
        self.settup_dbs()

    def settup_dbs(self):
        self.settup_client_db()
        self.settup_file_db()
        self.settup_job_db()

    def settup_client_db(self,):
        ''' Our 'relfective' database that handles foreign connections'''
        settings = self.settings.client_db
        db_url = settings.db_standard + settings.db_loc._swapped_slash_dir
        settings.db_loc.ensure_dir()
        # raise Exception(db_url)
        self.Client_DB_Engine  = create_engine(db_url)
        self.Client_DB_Session = sessionmaker(bind=self.Client_DB_Engine)
        # self.file_db_session = self.Session()
        set_listeners_on_tables(list(Client_DB_Model.__subclasses__()), self.events)
        Client_DB_Model.metadata.create_all(self.Client_DB_Engine)
        #self.services_pool.Extend(Client_DB_Services)
        #self.event_handler.Extend(Client_DB_Events  )

        self.session           = self.Client_DB_Session()
        self.client_db_session = self.session
        #HACK. Change to make contextual database sessions as per good practice

    def settup_file_db(self,):
        ''' The database-storage that handles Files and similar '''
        self.settings.file_db.db_loc
        self.settings.file_db.storage

        settings = self.settings.file_db
        db_url = settings.db_standard + settings.db_loc._swapped_slash_dir
        settings.db_loc.ensure_dir()
        
        self.File_DB_Engine  = create_engine(db_url)
        self.File_DB_Session = sessionmaker(bind=self.File_DB_Engine)
        # self.file_db_session = self.Session()
        set_listeners_on_tables(list(File_DB_Model.__subclasses__()), self.events)
        File_DB_Model.metadata.create_all(self.File_DB_Engine)
        

    def settup_job_db(self,):
        ''' The local Job database-storage that handles each task and working files. '''
        self.settings.job_db.db_loc
        self.settings.job_db.storage

        settings = self.settings.job_db
        db_url = settings.db_standard + settings.db_loc._swapped_slash_dir
        settings.db_loc.ensure_dir()
    
        self.Job_DB_Engine  = create_engine(db_url)
        self.Job_DB_Session = sessionmaker(bind=self.Job_DB_Engine)
        # self.file_db_session = self.Session()
        set_listeners_on_tables(list(Job_DB_Model.__subclasses__()), self.events)
        Job_DB_Model.metadata.create_all(self.Job_DB_Engine)

    # @Events.Sub('after_insert')
    # @Events.Sub('after_update')
    # @Events.Sub('after_delete')
    # def test_update_client(self,event, event_key, container, *args,**kwargs):
    #     for websocket in self.manager_websocket_pool.slice(id='state_info'):
    #         websocket : Manager_Websocket_Wrapper_Base
    #         asyncio.run(websocket.close())

class Worker_Local(Local_Common, Local_Entity_Base):
    _Fapi_Dep_Path = '/Worker_Statics'
    Events = Event_Router.New()
    Entity_Type   = Entity_Types.WORKER
    SettingsType  = Worker_Settings
    InterfaceType = Worker_Interface
    settings      : Worker_Settings
    
    def __init__(self, settings_loc:str='./worker_settings.yaml'):
        self.events = self.Events(self)
        self.interface              = self.InterfaceType(self)
        self.manager_websocket_pool = Manager_Websocket_Pool()
        self.client_websocket_pool  = Client_Websocket_Pool()
        self.load_settings(settings_loc)
        # self.load_context_settings()
            #TODO: Context settings, ie machine ID
        self.uid = 'TestWorker'
        #self.services_pool = ServicesPoolType(self)
        #self.event_handler = EventHandlerType(self)
        self.settup_client_db()
        self.create_manager()

    def settup_client_db(self,):
        ''' Our 'relfective' database that handles foreign connections'''
        settings = self.settings.client_db
        db_url = settings.db_standard + settings.db_loc._swapped_slash_dir
        settings.db_loc.ensure_dir()
        self.Client_DB_Engine  = create_engine(db_url)
        self.Client_DB_Session = sessionmaker(bind=self.Client_DB_Engine)
        set_listeners_on_tables(list(Client_DB_Model.__subclasses__()), self.events)
        Client_DB_Model.metadata.create_all(self.Client_DB_Engine)

        self.session           = self.Client_DB_Session()
        self.client_db_session = self.session
        #HACK. Change to make contextual database sessions as per good practice

    def create_manager(self):
        self.client_db_session.merge(Manager_Foreign(
            uid  = 'MANAGER_SINGLTON',
            host = self.settings.manager.addr,
            port = self.settings.manager.port,
        ))
        self.client_db_session.commit()

    def fapi_lifespan(self, app):
        self.connect_to_manager()
        yield

    @Events.Schedule(auto_run = True, interval = 5)
    async def connect_to_manager(task,self):
        manager = self.client_db_session.query(Manager_Foreign).first()
        manager : Manager_Foreign
        try:
            i = 0
            while task.continue_execution:
                print('ATTEMPTING TO CONNECT TO MANAGER')
                i = i + 1
                if  i > 4: 
                    print('MAX ATTEMPTS EXCEEDED')
                    break
                with manager.Active(), self.Active():
                    # sucess = manager.worker_interface.test()
                    sucess = await manager.worker_interface.worker_websocket()
                    if sucess is not None: 
                        print('FOUND!')
                        break 
                yield
        except GeneratorExit:
            print('CANCLED ATTEMPTS TO CONNECT TO MANAGER')
            ... #Should not hit in forever use case
        

class Foreign_Common():
    def __repr__(self):
        return f'< {self.Entity_Type} | {self.host}:{self.port} @ row {self.uid} > '

    def __init__(self, uid, host, port):
        self.uid  = uid
        self.host = host
        self.port = port

    def export_header(self, from_entity:Local_Entity_Base)->dict:
        return {}
    
    def intake_request(self, request, header):
        self.port = request.client.port
        self.host = request.client.host
        
    def matches_request(self,request:Request, headers:Request.headers):
        return all([headers.get('Role', default = '') == self.Entity_Type.value,
                    headers.get('UID',  default = '') == self.uid])

    def export_auth(self,from_entity)->tuple:
        return tuple()
    
    @classmethod
    def New_From_Request(cls,local_entity, request):
        return cls(request.headers.get('UID'), request.client.host, request.client.port)
    
class Client_Foreign(Foreign_Common,Foreign_Entity_Base, Client_DB_Model):
    Entity_Type   = Entity_Types.CLIENT
    __tablename__ = Entity_Types.CLIENT.value
    interface     = Manager_Interface_Info()

    uid       = Column(String, primary_key=True)
    host      = Column(String)
    port      = Column(String)
    con_state = Column(Sql_Enum(Connection_States), default = Connection_States.NEVER_CON)
    _trust : Trust_States = Trust_States.TRUSTED
        #TODO: CHANGE LATER TO BE SECURE

class Manager_Foreign(Foreign_Common,Foreign_Entity_Base, Client_DB_Model):
    Entity_Type      = Entity_Types.MANAGER
    __tablename__    = Entity_Types.MANAGER.value
    interface        = Manager_Interface_Info()
    worker_interface = Manager_Worker_Interface()
    
    uid       = Column(String, primary_key=True)
    host      = Column(String)
    port      = Column(String)
    con_state = Column(Sql_Enum(Connection_States), default = Connection_States.NEVER_CON)
    _trust : Trust_States = Trust_States.TRUSTED
        #TODO: CHANGE LATER TO BE SECURE


class Worker_Foreign(Foreign_Common,Foreign_Entity_Base, Client_DB_Model):
    __tablename__ = Entity_Types.WORKER.value
    Entity_Type   = Entity_Types.WORKER
    
    uid       = Column(String, primary_key=True)
    host      = Column(String)
    port      = Column(String)
    con_state = Column(Sql_Enum(Connection_States), default = Connection_States.NEVER_CON)
    _trust : Trust_States = Trust_States.TRUSTED
        #TODO: CHANGE LATER TO BE SECURE


ROLE_TABLE_MAPPING = {
    Manager_Foreign.Entity_Type.value : Manager_Foreign,
    Worker_Foreign.Entity_Type.value  : Worker_Foreign ,
}