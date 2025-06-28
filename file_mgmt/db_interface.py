from .db_struct import (asc_Space_NamedFile, asc_Space_NamedSpace, File, Space, target, Export, Session, User)
from   typing import Any
import typing
import yaml
import os
import atexit

class _settings_base:
    ''' dataclass that interprets a settings_object or custom start kwargs '''

    imported_keys : list[str] #keys corrisponding to values that have been imported
    __anno_resolved__ : dict[str,Any]

    def __init__(self):
        ...
    
    def export_yaml_recur(self,export_defaults=False)->dict:
        ''' Export yaml recursivly w/a based on hasattr(self,k,export_yaml_recur). Otherwise record straight (Non strict) '''
        self.ensure_type_hints()
        class _empty: ...
        res = {}
        
        for k,ty in self.__anno_resolved__:
            v = getattr(self,k,_empty)
            if v is _empty:
                continue
            elif k not in self.imported_keys and not export_defaults:
                continue
            elif func := getattr(v,'export_yaml_recur'):
                res[k] = func(export_defaults)
            else:
                res[k] = v
        
        return res

    def load_file(self,fp:str):
        assert fp.endswith('.yaml') or fp.endswith('.yml')
        with open(fp,'r') as file:
            data = yaml.safe_load(file)
            self.set_attributes(data)

    def save_file(self,export_fp:str,overwrite=False):
        ''' Exporting a file, will not overwrite by default '''
        
        assert os.path.isfile(export_fp)

        if overwrite and os.path.file_exists(export_fp):
            raise Exception('File exists! Remove file or rerun func with overwrite = True')
        
        os.make_dirs(os.path.split(export_fp)[0], exist_ok = True)

        data = self.export_yaml_recur()

        with open(export_fp, 'w', encoding='utf8') as file:
            yaml.dump(data, file, default_flow_style=False, allow_unicode=True)

    def set_attributes(self,data:dict):    
        self.ensure_type_hints()

        applied_keys = []
        for k,v in data.items():
            applied_keys.append(k)
            if k in self.__anno_resolved__.keys():
                ty = self.__anno_resolved__[k]
                try:
                    setattr(self,k,ty(v))
                except:
                    raise Exception(f'Key "{k}" with value "{v}" was not about to be converted!')
            else:
                raise Exception(f'Key "{k}" is not defined in the settings_interface! Perhaps you ment to have it as a sub object variable?')
        
        unapplied_keys = [k for k in self.__anno_resolved__.keys() if (k not in applied_keys) and (not getattr(self,k,None))]
        defaulted_keys = [k for k in self.__anno_resolved__.keys() if (k not in applied_keys) and (getattr(self,k,None))]

        if unapplied_keys:
            raise Exception(f'Following values were not imported and are required: /n {unapplied_keys}')

        if defaulted_keys:
            print('Following keys were not imported and resolved to default values:')
            for k in defaulted_keys:
                print(f'{k} has defaulted to: f{getattr(self,k)}')
        
        self.imported_keys = applied_keys

    def ensure_type_hints(self):
        if not hasattr(self.__anno_resolved__):
            self.__anno_resolved__ = typing.get_type_hints(self)

class _context_variable_base(_settings_base):
    ''' Platform Context Variable '''
    #Consider complex version as a grid matrix?
    def __init__(self, values:str|dict):
        if isinstance(values,str):
            for k in self._keys:
                setattr(self,k,values)
        else:
            self.set_attributes(values)
            
    def get_value(self,context:str):
        class _empty:...
        if v := self.getattr(self,context.lower(),_empty) != _empty:
            return v
        elif getattr(self,'default',_empty) != _empty:
            return self.default
        else:
            raise Exception(f'Context argument "{context}" nor is a default defined for this context value!')
    
    def __getitem__(self,k):
        return self.get_value(k)

    _keys = ['default']
    default:str

    def __repr__(self):
        injection = {}

        class _empty:...
        for k in self._keys:
            if (v:=self(getattr(self,k,_empty))) != _empty:
                injection[k] = v

        return f'< Context_Varaible Object: {injection}>'


class platform_context_variable(_context_variable_base):
    _keys = ['default','windows','linux']
    default : str
    windows : str
    linux   : str

pcv = platform_context_variable

class settings_interface(_settings_base):
    database_fp   : str
    cache_dir     : str = './cache/'
    logging_dir   : str = './logs/'
    lock_location : str = './'
    facing_dir    : pcv = pcv({'Windows':'./face_win/','Linux':'./face_linux/'})    #converted on import


class db_interface():
    ''' Interface for managing the file database directly. Each instance is a locked session with a specific db. DBs should not have overlapping cached files '''
    def __init__(self,settings_file:dict|None=None,**kwargs):

        self.settings = settings_interface()
        if settings_file:
            self.settings.load_file(settings_file)
        elif kwargs:
            self.settings.set_attributes(kwargs)
        else:
            #Initilizes anyway, object throws warnings & exceptions w/a
            self.settings.set_attributes({})
        
        self.db_lock_check()
        self.db_lock_register()
        
    def db_lock_check(self):
        self.settings.lock_location

    def db_lock_register(self):
        self.settings.lock_location
        
    def db_lock_unregister(self):
        self.settings.lock_location
        