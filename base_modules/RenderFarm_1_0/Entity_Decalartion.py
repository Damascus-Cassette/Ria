

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

from .Web_Interface.API_V1_7 import (
                            Interface_Base      , 
                            Foreign_Entity_Base , 
                            Local_Entity_Base   ,
                            OL_IO               )

from fastapi         import (Request            ,             
                            FastApi             )

from Entity_Settings import(Manager_Settings    ,
                            Worker_Settings     )

from pathlib         import Path               
from enum            import Enum               
import yaml

class Entity_Types(Enum):
    CLIENT  = 'CLIENT' 
    MANAGER = 'MANAGER'
    WORKER  = 'WORKER' 
    UNDEC   = 'UNDEC'

class Entity_States(Enum):
    STARTUP    = 'STARTUP'
    OPERATING  = 'OPERATING'
    

Base = declarative_base()
class UNDEC_Foreign(Foreign_Entity_Base,Base):
    ''' Undeclared base class, ie a default entity '''
    __tablename__ = Entity_Types.UNDEC.value 
    _interactive  = False
    Entity_Type   = Entity_Types.UNDEC

    def __init__(self,host,port):
        self.host = host
        self.port = port

    id  = Column(Integer, primary_key=True)
    host = Column(String)
    port = Column(String)

    def __repr__(self):
        return f'< {self.Entity_Type} | {self.host}:{self.port} @ row {self.id} > '

    def matches_request(self, request:Request, headers:Request.headers):
        return all([
            str(self.host) == str(request.client.host),
            # str(self.port) == str(request.client.port),
        ])

    def intake_request(self, request:Request, headers:Request.headers):
        self.port = request.client.port
            
    @classmethod
    def New_From_Request(cls, request):
        return cls(request.client.host, request.client.port)


class Manager_Client_Interface(Interface_Base):
    Router_Subpath = 'cl'
    
class Manager_Worker_Interface(Interface_Base):
    Router_Subpath = 'wk'
    #create websockets posting of tasks here

class Manager_Interface(Interface_Base):
    ''' Manager interface that should give state and the like '''
    worker_interface = Manager_Worker_Interface
    client_interface = Manager_Client_Interface
    
class Local_Manager(Local_Entity_Base):
    Entity_Type  = Entity_Types.MANAGER
    Entity_State = Entity_States.STARTUP
    Interface    = Manager_Interface
    SettingsType = Manager_Settings

    def __init__(self, settings_fp:str):
        self.settings_fp = settings_fp
    

    manager_db_engine        : EngineType
    manager_db_SessionType   : SessionType

    database_db_engine       : EngineType
    database_db_SessionType  : SessionType

    def create_app(self):
        app = FastApi()
        self.attach_to_app       (app)
        self.attach_to_app_events(app)
        return app
    
    def attach_to_app_events(self,app:FastApi):
        if func:=getattr(self,'app_on_startup' ): app.event('on_startup' )(func)
        if func:=getattr(self,'app_on_shutdown'): app.event('on_shutdown')(func)

    def app_startup(self):
        self.ensure_settings(self.settings_fp)
        self.load_settings  (self.settings_fp)

        self.ensure_manager_db()
        self.load_manager_db()
        self.load_manager_db_jobs()

        self.Entity_State = Entity_States.OPERATING
        
    def export_header(self, to_entity:Foreign_Entity_Base)->dict:
        return {'Role'  : self.Entity_Type.value  , 
                'UID'   : self.unique_id          ,
                'State' : self.Entity_State.value }

    def ensure_settings(self,filepath):
        ''' If settings do not exist, make. 
        File may contain settings that have to be edited before load. 
        May desire to halt load and throw exception due to this  '''

        if not Path(filepath).exists:
            with open(filepath,'w') as file:
                defaults = self.SettingsType()._export_()
                yaml.dump(defaults,file)

    def load_settings(self,filepath):
        ''' Load settings into structure settings '''
        with open(filepath,'r') as file:
            settings : dict = yaml.load(file)
            self.settings = self.SettingsType._import_(settings)
     

    def ensure_manager_db(self,):
        ''' Ensure that the manager database exists, loading loc from settings file. '''
    def load_manager_db(self,):
        ''' Load the manager db '''

    def load_manager_db_jobs(self):
        ''' create session and update from Job db folder structure '''

