
# class _Event_Item_Wrapper():

#     def __init__(self,Event_Item_Constructed):
#         ...

#     def attach(self,router):
#         ...
    
#     def __get__():
#         ...    

from types import FunctionType
from typing import Self
from enum import Enum
from inspect import isclass
from functools import partial
class _Event_Types(Enum):
    PUB      = 'PUB' 
    SUB      = 'SUB' 
    BUFFER   = 'BUFFER' 
    READER   = 'READER' 
    SCHEDULE = 'SCHEDULE'

    META_SUB = 'META_SUB'       #Meaning Router Events that happen local only 


class Event_Item():
    ''' Wrapper classes instanced on each item. 
    Due to Order of operations, __get__ does not work unless it it's directly on the parent class 
    Considering using an Event_Item_Wrapper class to operate as an instance-buffer.
    '''

    func : FunctionType

    @classmethod
    def New(cls, router:'Event_Router', mode:_Event_Types, func, event_key='', **w_kwargs):
        new = type(f'Constructed_Event_Item:{mode.value}', (Event_Item,), w_kwargs)
        new.router_cls  = router
        new.mode        = mode
        new.event_key   = event_key
        new.func        = staticmethod(func)
        new.w_kwargs    = w_kwargs
        return new

    def __init__(self,router_inst):
        self.router = router_inst
        self.router.event_children[self.mode].append(self)
        
        if isclass(self.func):
            if issubclass(self.func,Event_Item): 
                self.func = self.func(router_inst)

    def __call__(self, container,*args,**kwargs):
        match self.mode:
            case _Event_Types.PUB:
                res = self.func(container,*args,**kwargs)
                self.router.publish(self,self.event_key, container, **self.w_kwargs)
                return res

            case _Event_Types.SUB:
                return self.func(container,*args,**kwargs)

            case _:
                raise Exception(f'UNKNOWN MATCH: {self.mode}')

class _def_dict_list(dict):
    def __missing__(self,key):
        self[key] = inst = []
        return inst

class Event_Router():
    Constructed     = False
    
    router_parent   : Self|None
    router_children : list 

    Event_Children  : _def_dict_list  # Children on construction  add themselves to this dict[Enum|list]
    event_children  : _def_dict_list  # Children on instanciation add themselves to this dict[Enum|list]

    @classmethod
    def New(cls):
        new = type(f'Constructed_Event_Router', (Event_Router,), {})
        new.Constructed     = True
        new.Event_Children  = _def_dict_list()
        return new

    @classmethod
    def Pub(cls,event_key, filter = None, local_only:bool=False): 
        return cls.create_wrapper(_Event_Types.PUB, event_key, filter=filter, local_only=local_only)
    @classmethod
    def Sub(cls,event_key, filter = None, local_only:bool=False): 
        return cls.create_wrapper(_Event_Types.SUB, event_key, filter=filter, local_only=local_only)

    @classmethod
    def create_wrapper(cls,mode,event_key,*args,**kwargs):
        assert cls.Constructed
        def wrapper(func):
            new = Event_Item.New(cls, mode, func,event_key, *args,**kwargs)
            cls.Event_Children[mode].append(new)
            return new
        return wrapper

    def __init__(self, container, parent=None):
        self._container      = container
        self.router_parent   = parent
        self.router_children = []
        self.event_children  = _def_dict_list()
        self._format_container(container)

    def _format_container(self,container):
        ''' Ensure that all Event_Item children are instanciated '''
        for k in dir(container):
            if k.startswith('__'): continue
            v = getattr(container, k)
            # if v in self.Event_Children.any:
            print(v,v.__class__.__bases__)
            if getattr(v,'router_cls',None) is self.__class__: 
                setattr(container,k,partial(v(self),container))
        self._format_readers()
    
    def _format_readers(self):
        for buffer in self.event_children[_Event_Types.BUFFER]:
            for reader in self.event_children[_Event_Types.READER]:
                if buffer.__class__ is reader.Buffer_Parent_Cls:
                    buffer.readers.append(reader)
                    reader.buffer = buffer
    
    def publish(self, event, event_key, container, filter=None, local_only=False):
        if filter is not None:
            if filter(self._container,event_key,container): 
                return
        
        if self.router_parent and (not local_only):
            self.publish(event,event_key,container)
            return

        self.call_subs(event, event_key, container, is_local=True, local_only=local_only)

    def call_subs(self, event, event_key, container, is_local:bool=False, local_only=False):
        for x in self.event_children[_Event_Types.SUB]:
            if x.event_key != event_key:
                continue
            if (not is_local) and x.local_only:
                continue
            if x.filter is not None:
                if not x.filter(self._container,event_key,container):
                    continue
            x(self._container, event, event_key, container)

        if not local_only:
            for x in self.router_children:
                x.call_subs(event,event_key,container)