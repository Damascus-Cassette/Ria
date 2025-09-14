''' Entity local and foreign declaration, Foregin is the non-local interface of a connection by declared entity typ '''

import os
import yaml
import asyncio
from fastapi.responses import HTMLResponse
from pathlib import Path
from contextvars import ContextVar

from fastapi                        import (Request, Response, APIRouter, WebSocket as WebSocket_Manager)
from sqlalchemy                     import (Column, Boolean, ForeignKey, Integer, String, create_engine, Table, Engine as EngineType, Enum as Sql_Enum, )
from sqlalchemy.orm                 import (declarative_base, relationship, sessionmaker, Mapped, mapped_column ,Session as SessionType)

from .Job_Database_Model            import Base as Job_DB_Model
from .FileDB                        import Base as File_DB_Model

from .Statics                       import Entity_Types, Trust_States, Connection_States, ActionState_Message_Actions

from ..Web_Interface.API_V1_8       import Foreign_Entity_Base, Local_Entity_Base
from ..Web_Interface.Websocket_Pool import Client_Websocket_Pool,Manager_Websocket_Pool

from .Entity_Settings               import Manager_Settings, Worker_Settings, Client_Settings
from .Entity_Settings_Common        import CURRENT_DIR

from .EventSystem.Struct_Pub_Sub_v1_2          import Event_Router
from .EventSystem.Pub_Sub_Sql_Events_Factory   import set_listeners_on_tables

from .Interface_Manager   import Manager_Interface_Info, Manager_Worker_Interface
from .Interface_Worker    import Worker_Interface
from .Interface_FileDB    import FileDB_Interface


from .Bidi_Websocket import (
    Message_Commands_Client  , Message_Commands_Manager , Message_Commands_Worker  ,
    message_interface_common as Message_Interface_Client , message_interface_common as Message_Interface_Manager , message_interface_common as Message_Interface_Worker ,
    )

from copy import copy

from typing import Any

Client_DB_Model = declarative_base()


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
    Entity_Type     = Entity_Types.MANAGER
    Events          = Event_Router.New(readout=True)
    _Fapi_Dep_Path  = '/Manager_Statics'


    InterfaceType          = Manager_Interface_Info
    interface              : Manager_Interface_Info

    WorkerInterfaceType    = Manager_Worker_Interface
    worker_interface       : Manager_Worker_Interface

    FileDB_InterfaceType   = FileDB_Interface
    filedb_interface       : FileDB_Interface

    BidiInterfaceType      = Message_Interface_Manager
    bidi_interface         : Message_Interface_Manager

    BidiCommandsType       = Message_Commands_Manager   # This one handles porting messages/commands
    bidi_commands          : Message_Commands_Manager   

    SettingsType           = Manager_Settings
    settings               : Manager_Settings

    manager_websocket_pool : Manager_Websocket_Pool
    client_websocket_pool  : Client_Websocket_Pool



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
        self.events = self.Events(self)
        self.interface              = self.InterfaceType(self)
        self.worker_interface       = self.WorkerInterfaceType(self)
        self.bidi_interface         = self.BidiInterfaceType(self)
        self.filedb_interface       = self.FileDB_InterfaceType(self)
        self.bidi_commands          = self.BidiCommandsType(self)

        self.manager_websocket_pool = Manager_Websocket_Pool()
        self.client_websocket_pool  = Client_Websocket_Pool()
        
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

from fastapi import FastAPI

class Worker_Local(Local_Common, Local_Entity_Base):
    Entity_Type            = Entity_Types.WORKER
    Events = Event_Router.New()
    _Fapi_Dep_Path = '/Worker_Statics'
    

    SettingsType           = Worker_Settings
    settings               : Worker_Settings
    

    InterfaceType          = Worker_Interface
    interface              : Worker_Interface

    BidiInterfaceType      = Message_Interface_Worker
    bidi_interface         : Message_Interface_Worker

    BidiCommandsType       = Message_Commands_Worker
    bidi_commands          : Message_Commands_Worker
    
    manager_websocket_pool : Manager_Websocket_Pool
    client_websocket_pool  : Client_Websocket_Pool
    
    def __init__(self, settings_loc:str='./worker_settings.yaml'):
        self.events = self.Events(self)
        self.interface              = self.InterfaceType(self)
        self.bidi_interface         = self.BidiInterfaceType(self)
        self.bidi_commands          = self.BidiCommandsType(self)
        
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
                    sucess = await manager.bidi_interface.connection()
                    if sucess is not None: 
                        print('FOUND!')
                        break 
                yield
        except GeneratorExit:
            print('CANCLED ATTEMPTS TO CONNECT TO MANAGER')
            ... #Should not hit in forever use case
        
# class Client_Local():...



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
        self.port = str(request.client.port)
        self.host = str(request.client.host)
        
    def matches_request(self,request:Request, headers:Request.headers):
        return all([headers.get('Role', default = '') == self.Entity_Type.value,
                    headers.get('UID',  default = '') == self.uid])

    def export_auth(self,from_entity)->tuple:
        return tuple()
    
    @classmethod
    def New_From_Request(cls, local_entity, request):
        return cls(request.headers.get('UID'), request.client.host, request.client.port)
    
class UNDEC_Foreign(Foreign_Common,Foreign_Entity_Base, Client_DB_Model):
    '''UNREGISTERED & UNTRUSTED CONNECTION, CLIENTS WILL BE DEFINED ELSEWHERE AND ALWAYS PASS IN UID + SEC KEY'''
    __tablename__ = Entity_Types.UNDEC.value 
    Entity_Type   = Entity_Types.UNDEC
    _interactive  = False

    def __init__(self,host,port):
        self.host = host
        self.port = port

    uid  = Column(Integer, primary_key=True)
    host = Column(String)
    port = Column(String)
    con_state = Connection_States.NEVER_CON

    def matches_request(self, request:Request, headers:Request.headers):
        return all([
            str(self.host) == str(request.client.host),
        ])

    def intake_request(self, request:Request, headers:Request.headers):
        self.host = str(request.client.host)
        self.port = str(request.client.port)
    
    @classmethod
    def New_From_Request(cls, local_entity, request):
        return cls(request.client.host, request.client.port)

class Manager_Foreign(Foreign_Common,Foreign_Entity_Base, Client_DB_Model):
    Entity_Type      = Entity_Types.MANAGER
    __tablename__    = Entity_Types.MANAGER.value
    interface        = Manager_Interface_Info()
    worker_interface = Manager_Worker_Interface()
    bidi_interface   = Message_Interface_Manager()

    
    uid       = Column(String, primary_key=True)
    host      = Column(String)
    port      = Column(String)
    con_state = Column(Sql_Enum(Connection_States), default = Connection_States.NEVER_CON)
    action_state = Column(Sql_Enum(ActionState_Message_Actions), default = ActionState_Message_Actions.UNKNOWN)
    _trust : Trust_States = Trust_States.TRUSTED
        #TODO: CHANGE LATER TO BE SECURE

class Worker_Foreign(Foreign_Common,Foreign_Entity_Base, Client_DB_Model):
    __tablename__ = Entity_Types.WORKER.value
    Entity_Type   = Entity_Types.WORKER
    bidi_interface   = Message_Interface_Worker()

    
    uid       = Column(String, primary_key=True)
    host      = Column(String)
    port      = Column(String)
    con_state = Column(Sql_Enum(Connection_States), default = Connection_States.NEVER_CON)
    action_state = Column(Sql_Enum(ActionState_Message_Actions), default = ActionState_Message_Actions.UNKNOWN)
    _trust : Trust_States = Trust_States.TRUSTED
        #TODO: CHANGE LATER TO BE SECURE

class Client_Foreign(Foreign_Common,Foreign_Entity_Base, Client_DB_Model):
    Entity_Type   = Entity_Types.CLIENT
    __tablename__ = Entity_Types.CLIENT.value
    interface     = Manager_Interface_Info()
    bidi_interface   = Message_Interface_Client()


    uid       = Column(String, primary_key=True)
    host      = Column(String)
    port      = Column(String)
    con_state = Column(Sql_Enum(Connection_States), default = Connection_States.NEVER_CON)
    action_state = Column(Sql_Enum(ActionState_Message_Actions), default = ActionState_Message_Actions.UNKNOWN)
    _trust : Trust_States = Trust_States.TRUSTED
        #TODO: CHANGE LATER TO BE SECURE



ROLE_TABLE_MAPPING = {
    Manager_Foreign.Entity_Type.value : Manager_Foreign,
    Worker_Foreign.Entity_Type.value  : Worker_Foreign ,
    Client_Foreign.Entity_Type.value  : Client_Foreign ,
}