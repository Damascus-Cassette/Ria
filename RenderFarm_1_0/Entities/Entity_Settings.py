''' Entity settings, much inspired by the Blender Foundation's Flamneco's settings 

'''

from ...models.struct_file_io import BaseModel
from .Entity_Settings_Common import user_frmt_str, user_time_str, user_path
from pathlib import Path
# class Manager_Cache_Settings(BaseModel):
#     ''' Cache settings, for handling cache timeout and standards '''
# class Manager_Sec_Settings(BaseModel):
#     ''' Security Settings such as handshake rules and secrets. Defer to a later date ''' 
# class Manager_Worker_Settings(BaseModel):
#     ''' Settings for managing workers '''
#     timeout      : user_time_str = '1m'
class Manager_Task_Settings(BaseModel):
    ''' Settings for Job-Task management '''
    wk_task_timeout           : user_time_str = '10m'
    wk_task_fail_blocklist    : int           = 3
    task_softfail             : int           = 3


class Database_Settings(BaseModel):
    ''' Settings to expose the database through the manager '''
    _io_strict_ = False

    db_loc       : user_path = './filespace.db' 
    db_standard  : str       = 'sqlite:///' 
    storage      : user_path = './filespace/'   

    timeout_session  : user_time_str = 'MANUAL'

    #Timeout without a session/user
    timeout_export   : user_time_str = 'MANUAL'    
    timeout_import   : user_time_str = '30d'
    timeout_view     : user_time_str = '1h'

    timeout_space    : user_time_str = '3d'
    timeout_file     : user_time_str = '3d'

    timeout_metadata : user_time_str = '30d'
        # This is file/namedfile metadata that replaces the file on cleanup.
        # Used in recovery

class Job_DB_Settings(BaseModel):
    _io_strict_ = False

    db_loc       : user_path = './jobs.db'
    db_standard  : str       = 'sqlite:///' 
    storage      : user_path = './jobs/' 

class Manager_Client_DB_Settings(BaseModel):
    _io_strict_ = False
    db_loc      : user_path = './clients.db'
    db_standard : str       = 'sqlite:///'
    
class Manager_Settings(BaseModel):
    _io_strict_ = False

    ''' Settings for Manager's Operations '''
    # cache     : Manager_Cache_Settings
    # security  : Manager_Sec_Settings
    _log_level: int = 0

    root_dir  : user_path = './_manager'
        #Absolute, or Relative to CURRENTDIR.default,
        #Atm default is os.cwdir
    
    file_db   : Database_Settings 
    client_db : Manager_Client_DB_Settings
    job_db    : Job_DB_Settings   

    addr      : str  = '127.00.0.1'
    port      : str  = '4000'
    label     : str  = 'Ria Manager'

    def __init__(self):
        self.file_db   = Database_Settings() 
        self.client_db = Manager_Client_DB_Settings()
        self.job_db    = Job_DB_Settings()   
        super().__init__()

    worker_timeout : user_time_str = '1m' 

class Manager_Reference_Settings(BaseModel):
    ''' Find Manager, timout  '''
    _io_strict_ = False
    addr     : str = '127.0.0.1'
    port     : str = '4000'
    interval : int = 2

class Worker_Client_DB_Settings(BaseModel):
    _io_strict_ = False
    db_loc      : user_path = './worker-clients.db'
    db_standard : str       = 'sqlite:///' #

class Worker_Settings(BaseModel):
    ''' Settings for the Worker Entity '''
    _io_strict_ = False
    _profile_path     : str = '' #Override path to a Worker_Env_Settings
    _log_level        : int = 0

    client_db : Worker_Client_DB_Settings
    manager   : Manager_Reference_Settings

    def __init__(self):
        self.client_db = Worker_Client_DB_Settings()
        self.manager   = Manager_Reference_Settings()
    
    addr              : str  = '127.00.0.1'
    port              : str  = '4001'

    root_dir  : user_path = './_worker'

    # task_tags         : list = tuple() 
    # working_dir       : user_path = './working/'
    # working_dir_ext   : user_frmt_str = '/{job_id}/{task_id}/'

class Worker_Env_Settings(BaseModel):
    _io_strict_ = False
    UUID  : str = ''
    Label : str = ''

    def generate(self):
        ...


class Client_Settings(BaseModel):
    _io_strict_ = False
    ''' Interface to set settings through. May not use this directly, but we goforth '''
    ...