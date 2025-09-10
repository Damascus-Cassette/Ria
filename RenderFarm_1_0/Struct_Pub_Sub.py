from enum      import Enum

from typing    import Self,Any
from functools import wraps, partial
from types     import FunctionType
from inspect   import isclass,  iscoroutinefunction, isgeneratorfunction

import asyncio

class _Event_Types():
    PUB      = 'PUB' 
    SUB      = 'SUB' 
    META_SUB = 'META_SUB'       #Meaning Router Events that happen local only 
    BUFFER   = 'BUFFER' 
    READER   = 'READER' 
    SCHEDULE = 'SCHEDULE' 

class _def_dict_list(dict):
    def __missing__(self,key):
        self[key] = inst = []
        return inst

class Event_Pool():
    ''' '''
    ...

class Scheduled_Generator():
    def __init__(self, tick:int, func, args, kwargs, last_ran=None):
        ''' Last_ran will subtract from the first tick and execute now if negative '''
        assert isgeneratorfunction(func)
    
    
class Scheduled_Task():
    def __init__(self, tick:int, func, args, kwargs, last_ran=None):
        ''' Last_ran will subtract from the first tick and execute now if negative '''
        assert not isgeneratorfunction(func)

    def run_once(self):
        self.cont = True
        ...

    def run_forever(self):
        self.cont = True
        ...

    def generator_loop():
        ...
    
    def loop():
        ...

    def stop(self):
        self.cont = False
        if self.is_generator:
            return self.generator_tick():
        ...

    @property
    def is_running():
        ...


class Event_Item():
    Constructed = False
    BufferType  : Any
    Router_cls  : 'Event_Router'
    Event_Type  : _Event_Types
    Func        : FunctionType|Self
    Filter      : FunctionType|None

    router      : 'Event_Router'
    func        : FunctionType|Self
    buffer      : Any

    @classmethod
    def Reader(cls,*args,**kwargs):
        assert cls.Event_Type is _Event_Types.BUFFER
        assert cls.Constructed
        def wrapper(func):
            item = Event_Item.New(cls,_Event_Types.READER,func,*args,**kwargs)
            return item
        return wrapper
    
    @classmethod
    def New(cls, event_key, router_cls:'Event_Router', event_type:_Event_Types, func, *args, local_only = False, filter=None, buffertype=list, **kwargs):
        new = type('Event_Router_Constructed', (Event_Router,), {'Constructed':True})
        new.Event_Key   = event_key
        new.Constructed = True
        new.Filter      = filter
        new.Router_cls  = router_cls
        new.Event_Type  = event_type
        new.Func        = func
        new.Local_Only  = local_only    #Handled by router on publish. Only first level call is local. Otherwise pipes to root and then distributes through routers w/ filters applied
        new.BufferType  = buffertype
        new.Args        = args 
        new.Kwargs      = kwargs

        return new

    def __init__(self, router, nested = False):
        if not isclass(self.Func):
            self.func = self.Func
        elif issubclass(self.Func, Event_Item):
            self.func = self.Func(router, nested = True)
        
        if not nested:
            self.__get__ = self._get_

        self.readers = []
        self.router  = router

        router.attach_event_inst(self)
    
    def _get_(self,inst, inst_cls):
        ''' Only appplies after initialization IF this is not nested '''
        if inst is None:
            return self
        return partial(self,inst)
    
    def __call__(self,container,*args,**kwargs):
        match self.Event_Type:
            case _Event_Types.PUB:
                res = self.run_merged_coroutine(container,*args,**kwargs)
                self.router.Publish(self.event_key,container)
                return res
            case _Event_Types.SUB:
                return self.Func(container, *args, **kwargs)
            case _Event_Types.BUFFER:
                if not hasattr(self,'buffer'): self.buffer = self.BufferType()
                return self.Func(container, self.buffer *args, **kwargs)
            case _Event_Types.SCHEDULE:
                self.route.Schedule(self.func, self.Args, self.Kwargs, *args, **kwargs)


    def run_merged_coroutine(self,*args,**kwargs):
        ''' Try to run this function locally via asyncio'''
        if iscoroutinefunction(self.func):
            return asyncio.run(self.func(*args,**kwargs))
        else:
            return  self.func(*args,**kwargs)
        

class Event_Router():
    ''' Event Reciever and broadcaster. Can have filters for scope, as well as children.
    On inst it formats the parent class/inst to Connect the Event Items.
        - Done in this way to allow keeping the namespace, thought there are some better ways the class may be cosntructed or similar
        - ie, the pub-sib are not stored in the Event_Router, or inheritance-merged like the hooks system (at least atm, could be done)
            - Future allowences means I enforce the .New() constructor
    '''

    Constructed = False
    @classmethod
    def New(cls, filter = None)->Self:
        ''' Constructs a non-instanciated Event_Router'''
        new = type('Event_Router_Constructed', (Event_Router,), {'Constructed':True,'filter':filter})
        new.Event_Children = []
        return new
        
    @classmethod
    def Pub(cls, *args,**kwargs)->FunctionType:
        ''' Produces a Wrapper that on Execution will publish to the Event_Router.New() local source class instance. @Event.AutoRegister as a flag automatically attaches '''
        assert cls.Constructed
        def wrapper(func):
            item = Event_Item.New(cls,_Event_Types.PUB,func,*args,**kwargs)
            cls.Event_Children.append(item)
            return item
        return wrapper

    @classmethod
    def Sub(cls,*args,**kwargs)->FunctionType:
        ''' Produces a Wrapper that on Execution will attach to the Event_Router.New() source class. @Event.AutoRegister as a flag automatically attaches '''
        assert cls.Constructed
        def wrapper(func):
            item = Event_Item.New(cls,_Event_Types.SUB,func,*args,**kwargs)
            cls.Event_Children.append(item)
            return item
        return wrapper

    @classmethod
    def Meta_Sub(cls,*args,**kwargs)->FunctionType:
        ''' Produces a Wrapper that on Execution will attach to the Event_Router.New() source class. @Event.AutoRegister as a flag automatically attaches '''
        assert cls.Constructed
        def wrapper(func):
            item = Event_Item.New(cls,_Event_Types.META_SUB,func,*args,**kwargs)
            cls.Event_Children.append(item)
            return item
        return wrapper

    @classmethod
    def Schedule(cls,*args,**kwargs)->FunctionType:
        ''' Produces a Wrapper that on Execution will attach to the Event_Router.New() source class. @Event.AutoRegister as a flag automatically attaches '''
        assert cls.Constructed
        def wrapper(func):
            item = Event_Item.New(cls,_Event_Types.SCHEDULE,func,*args,**kwargs)
            cls.Event_Children.append(item)
            return item
        return wrapper

    @classmethod
    def Buffer(cls,*args,**kwargs)->FunctionType:
        assert cls.Constructed
        def wrapper(func):
            item = Event_Item.New(cls,_Event_Types.BUFFER,func,*args,**kwargs)
            cls.Event_Children.append(item)
            return item
        return wrapper

    def __init__(self,container,parent):
        self._container  = container
        self._parent     = parent
        if self._parent:
            self._parent.children_routers.append(self)

        self.event_insts = _def_dict_list()
        self.children_routers    = []

        self._format_container()
            #And create view / attach self to child_instance

    def _format_container(self,):
        for k in dir(self._container):
            if k.startswith('__'): continue
            v = getattr(self._container, k)
            if v in self.Event_Children:
                setattr(k,v(self))
        self._attach_readers()
    
    def _attach_readers(self):
        for buffer in self.event_insts[_Event_Types.BUFFER.value]:
            for reader in self.event_insts[_Event_Types.READER.value]:
                if isinstance(buffer.__class__, reader.Parent_Buffer_Cls):
                    buffer.readers.append(reader)
                    
    def attach_event(self, event):
        self.event_insts[event.Event_Type.value].append(event)
        
    def publish(self, key, event_container, original_container, _first_level=False, *args, **kwargs):
        ''' 
        - walk, check local if first level publish 
        - then push event key & args, kwargs to parent which should publish to root, 
        - which then if filters match, will then come back as an event call, and should push to all subs w/a 
        - Consider ContextVar method for preventing same executions of a subscriber
        '''
        ...

        self._meta_event('event_publishing_started', key, event_container,original_container, args, kwargs)
        if event_container.local_only and (event_container in self.event_insts):
            ''' catch local-only and trigger locals '''
            return self.event(self,key,event_container,original_container,args,kwargs,local_only=True)
        elif self._parent and _first_level:
            self.event(self,key,event_container,original_container,args,kwargs, local_only=True)
            self._parent.publish(key,event_container,original_container,args,kwargs)
        elif self._parent:
            self._parent.publish(key,event_container,original_container,args,kwargs)
        else:
            return self.event(self,key,event_container,original_container,args,kwargs)
        self._meta_event('event_publishing_complete', key, event_container,original_container, args, kwargs)

    def event(self,key,event_container, original_container, args, kwargs, local_only = False):
        ''' Event occurance under key, local_only=False triggers all that are not local. 
        Also checks filter for each Sub
        '''
        self._meta_event('sub_posting_started', key, event_container,original_container, args, kwargs)
        for sub in self.event_insts[_Event_Types.SUB.value]:
            if (local_only or sub.local_only) and (self._container != original_container): 
                continue
            if sub.filter:
                if not sub.filter(key,event_container,original_container,args,kwargs):
                    continue
            sub(self._container,key,*args,*kwargs)
        self._meta_event('sub_posting_complete', key, event_container,original_container, args, kwargs)

    def schedule(self,*args,**kwargs)->FunctionType:
        ''' Schedule a function using asyncio and return a callback to cancel the scheduled func. Also append locally to close. Optional on-close hook? '''
        raise NotImplementedError('STILL WORKING ON IT')

    def _meta_event(self, meta_event_key, event_key, event_container, orignal_container, args, kwargs):
        for sub in self.event_insts[_Event_Types.META_SUB.value]:
            sub(event_key, event_container, orignal_container, args, kwargs)


# class Eventable():
#     #Number of child events, uses __init__ to register children.
#     ...