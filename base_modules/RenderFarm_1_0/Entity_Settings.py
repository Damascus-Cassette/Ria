''' Entity settings, much inspired by the Blender Foundation's Flamneco's settings 

'''

from ...models.struct_file_io import BaseModel
from .Entity_Settings_Common import user_frmt_str, user_time_str
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
    database : str = './filespace.db' 
    storage  : str = './filespace/'   

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

class Manager_Settings(BaseModel):
    ''' Settings for Manager's Operations '''
    # cache     : Manager_Cache_Settings
    # security  : Manager_Sec_Settings
    _log_level: int = 0

    file_db   : Database_Settings

    addr      : str  = '127.22.0.1'
    port      : str  = '4000'
    label     : str  = 'Ria Manager'
    client_db : Path = './clients.db'
    job_db    : Path = './jobs.db'
    job_files : Path = './jobs/' 

    worker_timeout : user_time_str = '1m' 

class Worker_Settings(BaseModel):
    ''' Settings for the Worker Entity '''
    _profile_path     : str = '' #Override path to a Worker_Env_Settings
    _log_level        : int = 0

    addr              : str  = '127.22.0.1'
    port              : str  = '4001'

    task_tags         : list = tuple() 
    working_dir       : Path = './working/'
    working_dir_ext   : user_frmt_str = '/{job_id}/{task_id}/'

class Worker_Env_Settings(BaseModel):
    UUID  : str = ''
    Label : str = ''

    def generate(self):
        ...


class Client_Settings(BaseModel):
    ''' Interface to set settings through. May not use this directly, but we goforth '''
    ...