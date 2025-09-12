''' Static variables, such as storage locations, and user input types '''
from typing import Any
from enum   import Enum
from time   import time
from string import Formatter
from .EnvVars import CURRENT_DIR
# from ...models.struct_file_io import BaseModel
from pathlib import Path
from datetime import datetime

import os


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

    def _import_(self,data:str):
        self._data = data
    def _export_(self):
        return self._data


    _data : str|datetime|user_time_enums

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
     
    def _import_(self,data:str):
        self._data = data
    def _export_(self):
        return self._data

class user_path():
    ''' Possible relative path '''
    
    def _import_(self,data:str):
        self._data = data
    def _export_(self):
        return self._data

    def __init__(self,data:str):
        assert isinstance(data,str)
        self._data = data
    
    @property
    def data(self)->Path:
        if self._data.startswith('.'):
            return Path(str(CURRENT_DIR.get()) + self._data).resolve()
            # return Path(Path(CURRENT_DIR.get()) + Path(self._data)).resolve()
        return Path(self._data) 

    def __fspath__(self):
        return str(self.data)
    
    def __str__(self,):
        return str(self.data)
    
    def ensure_dir(self):
        path = self.data
        if not path.is_dir():
            path = Path(path.parents[0])
        if not path.exists():
            os.makedirs(path, exist_ok = True)

    @property
    def _swapped_slash_dir(self):
        ''' patch function for sqlalachemy, flipping backslashing '''
        return str(self).replace('/','\\')