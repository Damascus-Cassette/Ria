''' Entity local and foreign declaration, Foregin is the non-local interface of a connection by declared entity typ '''

from .Statics import Entity_Types
from ..Web_Interface.API_V1_8 import Foreign_Entity_Base, Local_Entity_Base, Interface_Base, IO
from ..Web_Interface.Websocket_Pool import Client_Websocket_Pool,Manager_Websocket_Pool,Manager_Websocket_Wrapper_Base
from sqlalchemy.orm import (declarative_base, sessionmaker, Session as SessionType)
from fastapi import APIRouter,WebSocket as WebSocket_Manager
# from ws4py.client.threadedclient import WebSocketClient as WebSocket_Client
import os
import yaml
from fastapi.responses import HTMLResponse
from .Entity_Settings import Manager_Settings
from pathlib import Path
from contextvars import ContextVar

from sqlalchemy     import (Column              ,
                            Boolean             ,
                            ForeignKey          ,
                            Integer             ,
                            String              ,
                            create_engine       ,
                            Table               ,
                            Engine as EngineType,
                            )

from sqlalchemy.orm import (declarative_base    , 
                            relationship        , 
                            sessionmaker        , 
                            Mapped              , 
                            mapped_column       ,
                            Session as SessionType)

from .Entity_Settings_Common import CURRENT_DIR

Client_DB_Model = declarative_base()

from .Job_Database_Model  import Base as Job_DB_Model
from ..File_Management    import File_DB_Model


class Manager_Interface(Interface_Base):

    @IO.Get(APIRouter,'/')
    def base_page(self, this_e, other_e, req):
        ...

    @IO.Websocket(APIRouter,'/state-info')
    async def state_info(self, this_e, other_e, websocket:WebSocket_Manager):
        await websocket.accept()


class Manager_Local(Local_Entity_Base):
    Entity_Type   = Entity_Types.MANAGER
    SettingsType  = Manager_Settings
    InterfaceType = Manager_Interface

    interface              : Manager_Interface
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

    def __init__(self, settings_loc:str='.manger_settings.yaml'):
        self.interface              = self.InterfaceType(self)
        self.manager_websocket_pool = Manager_Websocket_Pool()
        self.client_websocket_pool  = Client_Websocket_Pool()
        self.load_settings(settings_loc)
        #self.services_pool = ServicesPoolType(self)
        #self.event_handler = EventHandlerType(self)
        self.set_dbs()

    def set_settings(self,settings_loc):
        ''' Ensure settings exist, from calling directory if relative? '''
        if settings_loc.startswith('.'):
            settings_loc = Path(settings_loc).relative_to(CURRENT_DIR.get())
        
        if not Path(settings_loc).exists():
            settings = self.SettingsType()
            data = settings._export_()
            with open(settings_loc,'w') as f:
                yaml.dump(data,f)
            self.settings = settings
        else:        
            with open(settings_loc,'r') as f:
                data = yaml.load(f)
                self.settings = self.SettingsType()
                self.settings._import_(data)

        CURRENT_DIR.set(Path(self.settings.root_dir))
        #resolves root dir if relative to current path, settins as current dict
        #Must be done before other loading steps.

    def set_dbs(self):
        self.set_client_db()
        self.set_file_db()
        self.set_job_db()

    def set_client_db(self,):
        ''' Our 'relfective' database that handles foreign connections'''
        db_url = self.settings.client_db.db_loc
    
        self.CLient_DB_Engine  = create_engine(db_url)
        self.CLient_DB_Session = sessionmaker(bind=self.engine)
        # self.file_db_session = self.Session()

        Client_DB_Model.metadata.create_all(self.CLient_DB_Engine)
        #self.services_pool.Extend(Client_DB_Services)
        #self.event_handler.Extend(Client_DB_Events  )

    def set_file_db(self,):
        ''' The database-storage that handles Files and similar '''
        self.settings.file_db.db_loc
        self.settings.file_db.storage

        db_url = self.settings.client_db.db_loc
    
        self.File_DB_Engine  = create_engine(db_url)
        self.File_DB_Session = sessionmaker(bind=self.engine)
        # self.file_db_session = self.Session()

        File_DB_Model.metadata.create_all(self.File_DB_Engine)
        

    def set_job_db(self,):
        ''' The local Job database-storage that handles each task and working files. '''
        self.settings.job_db.db_loc
        self.settings.job_db.storage

        db_url = self.settings.client_db.db_loc
    
        self.Job_DB_Engine  = create_engine(db_url)
        self.Job_DB_Session = sessionmaker(bind=self.engine)
        # self.file_db_session = self.Session()

        Job_DB_Model.metadata.create_all(self.Job_DB_Engine)

class Manager_Foreign(Foreign_Entity_Base, Client_DB_Model):
    Entity_Type   = Entity_Types.MANAGER
    __tablename__ = Entity_Types.MANAGER.value
    interface = Manager_Interface


class Worker_Local(Local_Entity_Base):
    Entity_Type = Entity_Types.WORKER

class Worker_Foreign(Foreign_Entity_Base, Client_DB_Model):
    Entity_Type   = Entity_Types.WORKER
    __tablename__ = Entity_Types.WORKER.value