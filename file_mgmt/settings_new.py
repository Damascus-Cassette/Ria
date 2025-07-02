from contextvars import ContextVar
from contextlib  import contextmanager

from typing      import Any

class _common_root:
    ...

class _unset:
    ...

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

    def __init__(self,data=_unset):
        if not data is _unset:
            self.data = self.as_type(data)
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

    @classmethod
    def construct(cls, as_type, strict:bool, as_uuid:str|None=None, in_context:str|None=None, default:Any=None, default_args=None, default_kwargs=None):
        res = type('constructed_input',tuple([cls]),{
                        'strict'         : strict,
                        'as_type'        : as_type,
                        'as_uuid'        : as_uuid,
                        'in_context'     : in_context,
                        'default'        : default,
                        'default_args'   : default_args,
                        'default_kwargs' : default_kwargs,
                        })
        return res

class settings_dict_base(_common_root):
    
    _in_context : str|None #access inst of self in context under this attr string
    _as_uuid    : str|None #access inst of self in uuid list under this string
    
    def __init__(self,data:dict):

        used_keys   = []

        for k,v in vars(self).items():
            if issubclass(v,_common_root):
                if k in data.keys():
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
    
