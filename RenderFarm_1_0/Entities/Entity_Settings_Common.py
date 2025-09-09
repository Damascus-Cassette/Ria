''' Static variables, such as storage locations, and user input types '''
from typing import Any
from enum   import Enum
from time   import time
from string import Formatter
from .EnvVars import CURRENT_DIR
from pathlib import Path

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
            self._data = user_time_enums(data)
        else:
            self._data = data

    _data : time|user_time_enums

    @property
    def data(self):
        raise NotImplementedError('TODO')
        # TODO: CONVERT DATA AT READ

class user_frmt_str():
    def __init__(self,data:str|Any):
        data = str(data)
        self._data = data
    
    def _export_(self):
        return self._data

    def format(self,data:dict):
        ''' String formatter, typically dict produced from env & contextual variables. '''
        use_dict = {k:v for k,v in data if k in tuple(Formatter(data).parse())}
        return self._data.format_map(use_dict) 

class user_path():
    ''' Possible relative path '''
    
    def __init__(self,data:str):
        self._data = data
    
    def _export_(self):
        return self._data

    @property
    def data(self)->Path:
        if self.data.startswith('.'):
            return Path(Path(self._data).relative_to(CURRENT_DIR.get()))
        return Path(self._data) 
    
    def __str__(self,):
        return str(self.data)