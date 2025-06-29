from typing import Any
import typing
import yaml
import os
from contextvars import ContextVar
from contextlib  import contextmanager

missing_flag = '<! MISSING REQUIRED VALUE !>'
    #Consider adding type to missing value

class _standin_context:
    value : ContextVar = ContextVar('value',default = 'default') 


class _settings_base:
    ''' dataclass that interprets a settings_object or custom start, holds initialized repos '''
    context = context

    imported_keys : list[str] = []#keys corrisponding to values that have been imported

    __anno_resolved__ : dict[str,Any]

    strict = True           #Settings base, consider _tracked_attributes list?

    def __init__(self, values:dict|None=None):
        if values:
            self.set_attributes(values)
        else:
            ... #Is placeholder!

    def export_dict_recur(self,export_defaults=False)->dict:
        ''' Export yaml recursivly w/a based on hasattr(self,k,export_dict_recur). Otherwise record straight (Non strict) '''
        self.ensure_type_hints()
        class _empty: ...
        res = {}
        
        for k,ty in self.__anno_resolved__.items():
            v = getattr(self,k,_empty)
            if v is _empty and not export_defaults:
                continue
            elif v is _empty and export_defaults and self.strict:
                res[k] = missing_flag
            elif v is _empty and export_defaults and not self.strict:
                continue
            elif k not in self.imported_keys and not export_defaults:
                continue
            elif (func := getattr(v,'export_dict_recur',_empty)) != _empty:
                res[k] = func(export_defaults)
            else:
                res[k] = v
        
        return res

    def load_file(self,fp:str):
        assert fp.endswith('.yaml') or fp.endswith('.yml')
        with open(fp,'r') as file:
            data = yaml.safe_load(file)
            self.set_attributes(data)

    def save_file(self,export_fp:str,overwrite=False,export_defaults=False):
        ''' Exporting a file, will not overwrite by default '''
        
        assert os.path.isfile(export_fp)

        if  os.path.exists(export_fp) and not overwrite:
            raise Exception('File exists! Remove file or rerun func with overwrite = True')
        
        os.makedirs(os.path.split(export_fp)[0], exist_ok = True)

        data = self.export_dict_recur(export_defaults=export_defaults)

        with open(export_fp, 'w', encoding='utf8') as file:
            yaml.dump(data, file, default_flow_style=False, allow_unicode=True)

    def set_attributes(self,data:dict):    
        self.ensure_type_hints()

        applied_keys = []
        for k,v in data.items():
            if v == missing_flag:
                raise Exception(f'Key "{k}" is missing a required value! Settings file cannot load')
            
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

        if unapplied_keys and self.strict:
            raise Exception(f'Following values were not imported and are required: /n {unapplied_keys}')
        elif unapplied_keys and not self.strict:
            print(f'Warning! Following values were not imported: /n {unapplied_keys}')

        if defaulted_keys:
            print('Following keys were not imported and resolved to default values:')
            for k in defaulted_keys:
                print(f'{k} has defaulted to: f{getattr(self,k)}')
        
        self.imported_keys = applied_keys

    def ensure_type_hints(self):
        if not hasattr(self,'__anno_resolved__'):
            self.__anno_resolved__ = typing.get_type_hints(self)


class _context_variable_base(_settings_base):
    ''' Generic Context Varaible, initilized with context at declaration
     Fugly struct atm, consider something cleaner '''

    strict = False 

    context : Any
    _c_attr : str
    _d_attr : str
    _keys   : list = ['default']
    
    #Consider complex version as a grid matrix, or chained dicts
    def __init__(self, values:str|dict):
        if isinstance(values,str):
            for k in self._keys:
                setattr(self,k,values)
        else:
            self.set_attributes(values)
            
    def get(self):
        assert (cvar := getattr(self.context,self._c_attr,None)) != None
        return getattr(self, cvar.get(), getattr(self,self._d_attr))


    def __repr__(self):
        injection = {}

        class _empty:...
        for k in self._keys:
            if (v:=self(getattr(self,k,_empty))) != _empty:
                injection[k] = v

        return f'< Context_Varaible Object: {injection}>'

class context:
    #Fugly structure, consider something cleaner
    platform : ContextVar = ContextVar('platform',default = 'default') 
    
    @classmethod
    def set(cls,**kwargs):
        for k,v in kwargs.items():
            if (cvar:=getattr(cls,k,None)):
                cvar.set(v)
            else:
                raise Exception(f"Context could not be set for key {k} of value {v}")

class platform_context_variable(_context_variable_base):
    context = context
    _c_attr = 'platform'
    _d_attr = 'default'
    _keys   = ['default','windows','linux']

    default : str
    windows : str
    linux   : str

pcv = platform_context_variable

class db_info(_settings_base):
    context = context
    database_fp   : str
    cache_dir     : str = './cache/'
    logging_dir   : str = './logs/'
    lock_location : str = './'
    facing_dir    : pcv = pcv({'windows':'./face_win/','linux':'./face_linux/'})    #converted on import

class settings_interface(_settings_base):
    context = context
    strict = False
    database : db_info = db_info()


if __name__ == '__main__':
    import argparse
    import pprint
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file')
    parser.add_argument('-e', '--export',default=False,action='store_true')
    args = parser.parse_args()
    
    settings = settings_interface()
    if not args.export:
        settings.load_file(args.file)
        pprint.pprint(settings.export_dict_recur())
    if args.export:
        settings.save_file(args.file,overwrite=True,export_defaults=True)

