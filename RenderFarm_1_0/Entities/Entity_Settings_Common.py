''' Static variables, such as storage locations, and user input types '''
from typing import Any
from enum   import Enum
from time   import time
from string import Formatter

class user_time_enums(Enum):
    MANUAL = 'MANUAL'

class worker_profile_paths(Enum):
    WINDOWS = './TESTING' 
    LINUX   = './TESTING' #'/user/Ria/Ria_Worker_Settings.yaml'
    MAX     = './TESTING' 

class user_time_str():
    ''' User time input string, reads go-like format and optional MANUAL enum '''
    def __init__(self,data:str|Any):
        data = str(data)
        if data in user_time_enums._member_map_.keys():
            self.data = user_time_enums(data)
        else:
            self.data = data

    data : time|user_time_enums

class user_frmt_str():
    def __init__(self,data:str|Any):
        data = str(data)
        self.data = data
    
    def format(self,data:dict):
        ''' String formatter, typically dict produced from env & contextual variables. '''
        use_dict = {k:v for k,v in data if k in tuple(Formatter(data).parse())}
        return self.data.format_map(use_dict) 
    
