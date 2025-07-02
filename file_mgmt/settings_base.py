from contextvars import ContextVar
from contextlib  import contextmanager
from typing      import Any
import inspect
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
    def construct(cls, as_type, strict:bool=True, allow_blind=True, as_uuid:str|None=None, in_context:str|None=None, default:Any=None, default_args=None, default_kwargs=None):
        res = type('constructed_input',tuple([cls,_common_root]),{
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

    def __init__(self,data=_unset,):
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
            setattr(self.context, self.in_context, ContextVar(self.in_context, default=self))
        if self.as_uuid:
            self.uuid_map[self.as_uuid] = self
        
    def return_data(self):
        ''' Spot to place context evaluation & similar '''
        return self.data

    def __get__(self, instance, owner):
        return self.return_data()

    def __set__(self, instance, value):
        raise
    
    def get(self):
        return self.__get__(None,None)

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
        # assert isinstance(self.data,str)
        kwds = [k[1] for k in string.Formatter.parse("",self.data) if k[1]]
        kwds = {k:getattr(self.context,k).get().get() for k in kwds}
        return self.data.format(**kwds)
    

class settings_dict_base(_common_root):
    _in_context : str|None = None #access inst of self in context under this attr string
    _as_uuid    : str|None = None #access inst of self in uuid list under this string
    _required   : bool     = True

    def __init__(self,data:dict=_unset):
        if (data == _unset) and (self._required):
            print(f'data is {data} and is {_unset}')
            raise Exception(f'Catagory "{self.__class__}" is required!')
        if data is _unset:
            data = {}

        used_keys   = []

        cls_format_dict = {}

        for k,v in data.items():
            container = getattr(self,k)
            assert issubclass(container,_common_root)
            used_keys.append(k)

            if v == missing_flag:
                raise Exception(f'Missing required value in {self.__name__} : {k}')
            elif v == unset_v_flag:
                setattr(self,k,container())
                continue
            
            if issubclass(container,input_base): 
                cls_format_dict[k] = container(v)
            else:
                setattr(self,k,container(v))

        keys        = [k for k in dir(self)  if inspect.isclass(getattr(self,k)) and not k.startswith('__')]
        total_keys  = [k for k in keys       if issubclass(getattr(self,k),_common_root)]
        unused_keys = [k for k in total_keys if k not in used_keys]

        for k in unused_keys:
            print(f'WARNING! Unset Variable {k}, init with no args')
            container = getattr(self,k)
            if issubclass(container,input_base): 
                cls_format_dict[k] = container()
            else:
                setattr(self,k,container())

        self.context  = c_Context.get()
        self.uuid_map = c_uuids.get()

        if self._in_context:
            setattr(self.context,self._in_context,ContextVar(self._in_context,default=self))
        if self._as_uuid:
            self.uuid_map[self._as_uuid] = self

        unused_keys = [k for k in data.keys() if k not in used_keys]

        if unused_keys:
            print(vars(self))
            raise Exception(f'unused_keys!: {unused_keys}')
        
        new_base_name = self.__class__.__name__ + 'ChildClass'
        new_base = type(new_base_name, (self.__class__,), cls_format_dict)
        self.__class__ = new_base

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