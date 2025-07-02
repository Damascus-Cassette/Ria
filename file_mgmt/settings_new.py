from contextvars import ContextVar
from contextlib  import contextmanager
from typing      import Any
import json
import yaml
import string

class _common_root:
    ...    

class _unset(_common_root):

    ...

missing_flag = '<! MISSING REQUIRED VALUE !>'
unset_v_flag = '<! UNSET VALUE !>'

c_Context= ContextVar('Settings_Context' , default=None)
c_uuids  = ContextVar('Settings_uuid'    , default=None)

class input_base(_common_root):
    context        : Any
    uuid_map       : dict

    data           : Any

    strict         : bool      = True

    as_type        : Any 
    as_uuid        : str|None  = None 
    in_context     : str|None  = None 
    default        : Any       = None 
    default_args   : list[Any] = None
    default_kwargs : dict[Any] = None

    allow_blind    : bool      = True

    did_default    : bool      = True

    @classmethod
    def construct(cls, as_type, strict:bool, allow_blind=True, as_uuid:str|None=None, in_context:str|None=None, default:Any=None, default_args=None, default_kwargs=None):
        res = type('constructed_input',tuple([cls]),{
                        'strict'         : strict,
                        'as_type'        : as_type,
                        'as_uuid'        : as_uuid,
                        'in_context'     : in_context,
                        'default'        : default,
                        'default_args'   : default_args,
                        'default_kwargs' : default_kwargs,
                        'allow_blind'    : allow_blind,
                        })
        return res

    def __init__(self,data=_unset):
        if not data is _unset:
            self.data = self.as_type(data)
            self.did_default = False
        else:
            if self.default:
                self.data = self.as_type(self.default)
            elif self.default_args is not None or self.default_kwargs is not None:
                if not self.default_args: self.default_args   = []
                if not self.default_kargs: self.default_kargs = {}
                self.data = self.as_type(*self.default_args,*self.default_kwargs)
            elif self.strict:
                raise Exception('Missing Required Variable!')
            else:
                self.data = _unset

        self.context  = c_Context.get()        
        self.uuid_map = c_uuids.get()        

        if self.in_context:
            setattr(self.context,self._in_context,ContextVar(self.__name__,default=self))
        if self.as_uuid:
            self.uuid_map[self.as_uuid] = self
        
    def return_data(self):
        ''' Spot to place context evaluation & similar '''
        return self.data

    def __get__(self):
        return self.return_data()

    def __set__(self,value):
        raise
    
    def recursive_export(self,export_defaults:bool=False):
        if   (export_defaults and self.did_default) and (self.data is _unset):
            return unset_v_flag
        elif (export_defaults and self.did_default):
            return self.data
        elif not (export_defaults and self.did_default):
            return _unset
        elif not export_defaults and not self.did_default:
            return self.data
        else:
            raise

class input_context_formatted(input_base):
    def return_data(self):
        kwds = [l[1] for l in string.Formatter.parse(self.data)]
        kwds = {k:getattr(self.context,k).get() for k in kwds}
        return self.data.format(kwds)
    

class settings_dict_base(_common_root):
    _in_context : str|None #access inst of self in context under this attr string
    _as_uuid    : str|None #access inst of self in uuid list under this string
    
    def __init__(self,data:dict):

        used_keys   = []

        for k,v in vars(self).items():
            if issubclass(v,_common_root):
                if k in data.keys():
                    if data[k] == missing_flag: 
                        raise Exception(f'Missing Required Varaible for attr "{k}" !')
                    elif data[k] == unset_v_flag: 
                        setattr(self,k,v())
                    setattr(self,k,v(data[k]))
                    used_keys.append(k)
                else:
                    setattr(self,k,v())

        self.context  = c_Context.get()        
        self.uuid_map = c_uuids.get()        

        if self._in_context:
            setattr(self.context,self._in_context,ContextVar(self.__name__,default=self))
        if self._as_uuid:
            self.uuid_map[self._as_uuid] = self

        unused_keys = [k for k in data.keys() if k not in used_keys]

        assert not unused_keys

    @contextmanager    
    def loading_cm(context_obj:Any,uuid_map:dict):
        try:
            t1 = c_Context.set(context_obj)
            t2 = c_uuids.set(uuid_map)
            yield
        except:
            raise
        finally:
            c_Context.reset(t1)
            c_uuids.reset(t2)

    @classmethod
    def load_data(cls,data:dict,context=None,uuid_map=None):
        if context is None:
            context  = type('UnsetContext',tuple([]),{})
        if uuid_map is None:
            uuid_map = {}
        
        with cls.loading_cm(context,uuid_map):
            return cls(data)

    @staticmethod
    def load_yaml(fp):
        with open(fp,'r') as file:
            data = yaml.safe_load(file)
            return data

    @staticmethod
    def load_json(fp):
        with open(fp,'r') as file:
            data = json.loads(file)
            return data
    
    def recursive_export(self,export_defaults:bool=False):
        ret = {}
        for k,v in vars(self).items():
            if issubclass(v.__class__,_common_root):
                val = v.recursive_export(export_defaults=export_defaults)
                if val is _unset:
                    continue
                # if val == unset_v_flag: #or else
                ret[k] = val
        return ret
    
i_g = input_base.construct
i_f = input_context_formatted.construct

class test(settings_dict_base):

    var1 : str = i_g(str, as_uuid='var1', default='Var1Contents')
    var2 : str = i_f(str, as_uuid='var2', default='{var1}_DefaultString2')

    class nested(settings_dict_base):
        var3 : str = i_f(str, as_uuid='var3')