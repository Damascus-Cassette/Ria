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

    id   = Column(Integer, primary_key=True)
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

class Websocket_State_Info(Manager_Websocket_Wrapper_Base):
    Events = Event_Router.New()
    local_entity   : 'Manager_Local'
    foreign_entity : 'UNDEC_Foreign'

    # @Events.Sub(Events, Any)
    # @Events.Sub('after_delete')
    @Events.Sub('after_insert')
    def test_update_client(self, event, event_key, container, mapper, connection):
        self.event_buffer.append(('CREATE', 'clients' ,{'id':container.id, 'host':container.host, 'port':container.port,'label':getattr(container,'label')}))

    @Events.Sub('after_update')
    def test_update_client(self, event, event_key, container, mapper, connection):
        self.event_buffer.append(('CREATE', 'clients' ,{'id':container.id, 'host':container.host, 'port':container.port,'label':getattr(container,'label')}))
        
    def __init__(self, local_entity, foreign_entity, websocket, id=None, uid=None):
        super().__init__(local_entity, foreign_entity, websocket, id, uid)
        self.event_buffer = [
            ('BULK_CREATE','clients' , self.gather_all_undec()), #|self.gather_all_clients()
            ('BULK_CREATE','workers' , self.gather_all_workers()),
            ('BULK_CREATE','managers', self.gather_all_managers()),
            # ('BULK_CREATE','jobs',    self.gather_all_jobs( this_e.))
            # ('BULK_CREATE','tasks',   self.gather_all_tasks(this_e.))
        ]

    async def run(self):
        self.events = self.Events(self)
        self.remove_callback = self.local_entity.events.temp_attach_router_inst(self.events)
        # await self.accept()
        
        # while ((self.websocket.client_state is not Manager_WebSocketState.DISCONNECTED) and (not FAPI_SHUTTING_DOWN)) :

        while self.continue_execution:
            if self.event_buffer:
                event_buffer = copy(self.event_buffer)
                self.event_buffer.clear()
                for x in event_buffer:
                    await self.send_json(x)
            print('RUNNING')

            await asyncio.sleep(1)

        #This should send relevent db info on first call, then events take over. 
        #It may be a good idea to have a transient event_router

    
    def after_close(self):
        if hasattr(self,'remove_callback'):
            self.remove_callback()
        

    def gather_all_undec(self):
        res = []
        for row in self.local_entity.client_db_session.query(UNDEC_Foreign).all():
            res.append({'id':row.id, 'host':row.host, 'port':row.port })
        return res

    def gather_all_clients(self):
        res = []
        for row in self.local_entity.client_db_session.query(UNDEC_Foreign).all():
            res.append({'id':row.id, 'host':row.host, 'port':row.port })
        return res
    
    def gather_all_workers(self):
        res = []
        for row in self.local_entity.client_db_session.query(Worker_Foreign).all():
            res.append({'id':row.id, 'host':row.host, 'port':row.port })
        return res
 
    def gather_all_managers(self):
        res = []
        for row in self.local_entity.client_db_session.query(Manager_Foreign).all():
            res.append({'id':row.id, 'host':row.host, 'port':row.port })
        return res

    # def gather_all_jobs(self):
    #     res = []
    #     for row in self.local_entity.client_db_session.query(Job_DB_Model).all():
    #         res.append({'id':row.id, 'host':row.host, 'port':row.port })
    #     return res
    



class Manager_Interface(Interface_Base):
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
        await ws.run_with_handler()
        await ws.close()

class Worker_Interface(Interface_Base):
    ''' Worker interface is websocket msg : pub-sub based'''
    ...

class Local_Common():

    def export_header(self, to_entity:Foreign_Entity_Base)->dict:
        return {'Role': self.Entity_Type.value, 
                'UID' : self.unique_id}

    def export_header(self, to_entity:Foreign_Entity_Base)->dict:
        return {'Role': self.Entity_Type.value, 
                'UID' : self.unique_id}

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

        async def lifespan(app):
            yield
            FAPI_SHUTTING_DOWN.set(True)

        app = FastAPI(lifespan=lifespan)

        inst  = cls(*args,**kwargs)
        from fastapi.templating import Jinja2Templates
        inst.fapi_templates = Jinja2Templates(directory=inst._Fapi_Dep_Path)
        app.mount("/static", StaticFiles(directory=inst._Fapi_Dep_Path), name="static")

        @app.get("/url-list")
        def get_all_urls():
            url_list = [{"path": route.path, "name": route.name} for route in app.routes]
            return url_list

        return  inst.attach_to_app(app)

    # def fapi_mount_static(self,app):
    #     from fastapi import StaticFiles
    #     app.mount("/static", StaticFiles(directory="static"), name="static")
    #     ...

class Manager_Local(Local_Common,Local_Entity_Base):
    Entity_Type        = Entity_Types.MANAGER
    SettingsType       = Manager_Settings
    InterfaceType      = Manager_Interface

    Events             = Event_Router.New(readout=True)

    interface              : Manager_Interface
    settings               : Manager_Settings
    manager_websocket_pool : Manager_Websocket_Pool
    client_websocket_pool  : Client_Websocket_Pool

    @property
    def _Fapi_Dep_Path(self):
        #HACK make a root path argument that can change to unpack location when using NUITKA
        return f'{Path(__file__).parents[0]}/Manager_Statics'
         
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
    Entity_Type   = Entity_Types.WORKER
    SettingsType  = Worker_Settings
    InterfaceType = Worker_Interface
    settings      : Worker_Settings
    
    def __init__(self, settings_loc:str='./worker_settings.yaml'):
        self.interface              = self.InterfaceType(self)
        self.manager_websocket_pool = Manager_Websocket_Pool()
        self.client_websocket_pool  = Client_Websocket_Pool()
        self.load_settings(settings_loc)
        #self.services_pool = ServicesPoolType(self)
        #self.event_handler = EventHandlerType(self)

        self.connect_to_manager()

    def connect_to_manager(self,):
        ...

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
                    headers.get('UID',  default = '') == self.id])

    def export_auth(self,from_entity)->tuple:
        return tuple()
    
    @classmethod
    def New_From_Request(cls,local_entity, request):
        return cls(request.headers.get('UID'), request.client.host, request.client.port)
    

class Manager_Foreign(Foreign_Common,Foreign_Entity_Base, Client_DB_Model):
    Entity_Type   = Entity_Types.MANAGER
    __tablename__ = Entity_Types.MANAGER.value
    interface     = Manager_Interface()

    uid       = Column(Integer, primary_key=True)
    host      = Column(String)
    port      = Column(String)
    con_state = Column(Sql_Enum(Connection_States), default = Connection_States.NEVER_CON)
    _trust : Trust_States = Trust_States.TRUSTED
        #TODO: CHANGE LATER TO BE SECURE


class Worker_Foreign(Foreign_Common,Foreign_Entity_Base, Client_DB_Model):
    __tablename__ = Entity_Types.WORKER.value
    Entity_Type   = Entity_Types.WORKER
    
    uid       = Column(Integer, primary_key=True)
    host      = Column(String)
    port      = Column(String)
    con_state = Column(Sql_Enum(Connection_States), default = Connection_States.NEVER_CON)
    _trust : Trust_States = Trust_States.TRUSTED
        #TODO: CHANGE LATER TO BE SECURE


ROLE_TABLE_MAPPING = {
    Manager_Foreign.Entity_Type.value : Manager_Foreign,
    Worker_Foreign.Entity_Type.value  : Worker_Foreign ,
}