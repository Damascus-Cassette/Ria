'''A new iteration of the hook module that includes allowences in structure for the planned event system 
Clarity on terms within this project:
Hooks:   object's internal pre and post processors
Events:  Pre-Post event posting to a global list, directional
'''

from typing import Any,Self
from types  import FunctionType

from functools import wraps

class _shared_class():...

class _hook(_shared_class):
    def __init__(self ,
                func        :FunctionType|Self ,
                event       :str               ,
                /,*,
                key         :str    = None     ,
                anon        :bool   = None     ,
                mode        :str    = 'post'   ,
                see_args    :bool   = False    ,
                passthrough :bool   = False    ,
                ):
        self.hook_siblings   = []
        self.event_siblings  = []
        self.hooked_siblings = []
        if issubclass(func.__class__,_shared_class):
            self.hook_siblings  .extend(func.hook_siblings   )
            self.event_siblings .extend(func.event_siblings  )
            self.hooked_siblings.extend(func.hooked_siblings )
            func = func.func

        self.func        = func
        self.event       = event
        self.key         = key  if  key          else (func.__module__ + func.__name__)
        self.anon        = anon if (key or anon) else (True)
        self.mode        = mode
        self.see_args    = see_args
        self.passthrough = passthrough

    def __call__(self, *args, **kwargs):
        #May require __get__ with functools.partial to get container iirc
        # return self.func(*args,**kwargs)
        container : Hookable = args[0]
        return container._hooks.run_as_hook(self,args,kwargs)
            #This passthrough allows execution of sibling hooks and posting of events.

    @classmethod
    def wrapper(cls,**kwargs):
        def wrapper(func):
            return wraps(func)(cls(func,**kwargs))
        return wrapper


class _hooked(_shared_class):
    def __init__(self,
                 func:FunctionType|Self ,
                 event:str              ,
                 ):
        self.hook_siblings   = []
        self.event_siblings  = []
        self.hooked_siblings = []
        if issubclass(func.__class__,_shared_class):
            self.hook_siblings  .extend(func.hook_siblings   )
            self.event_siblings .extend(func.event_siblings  )
            self.hooked_siblings.extend(func.hooked_siblings )
            func = func.func
        self.func  = func
        self.event = event

    def __call__(self,*args,**kwargs):
        #May require __get__ with functools.partial to get container iirc
        #header is called, not a middle stack item.
        container : Hookable = args[0]
        return container._hooks.run_with_hooks(self,args,kwargs)
        
    @classmethod
    def wrapper(cls,**kwargs):
        def wrapper(func):
            return wraps(func)(cls(func,**kwargs))
        return wrapper

hook   = _hook  .wrapper
hooked = _hooked.wrapper


class hook_group():
    ''' Namespace and Anon merging on inheritance via a construction function, plus execution of hooks '''
    
    anon_funcs   : tuple
    named_funcs  : dict

    def __init__(self):
        self.anon_hooked  = tuple()
        self.named_hooked = {}

    def merge(self,other:Self):
        
        ...

    def run_with_hooks(self, hooked_inst:_hooked, container, func, args, kwargs):
        ''' Run a hooked function, runs with the hooks ascociated (also runs events on obj) '''
        #TODO

    def run_as_hook(self, hook_inst:_hook, container, func, args, kwargs):
        ''' Runs a function via it's hook (also runs events on obj & calls hooked w/a + throw error with recursive event triggering) '''
        #TODO

    def intake(self,obj:_shared_class):
        ''' Views any _hook,_hooked,_event object and determines if already inside and if anon vs not anon. Adds if does have '''
        #Also integrates all siblings
        #TODO

class Hookable():
    _hooks : hook_group
    def __init_subclass__(cls):
        ''' Create new hooks, integrate local with inherited or create from nothing if not here'''

        hg = hook_group()
        if (a:=getattr(cls, '_hooks',None)) is not None:
            hg.merge(a)
        cls._hooks = hg

        for k,v in cls.__dict__:
            if issubclass(v.__class__,_shared_class):
                hg.intake(v)


# def event_post():...
# def event_subscribe():...

from contextvars import ContextVar
if 0:

    add_me = ContextVar('addme',default=1)
    class mixin():
        @hook(event       = 'event_1',      #Hook event name. (Despite 'event' term this is always local to object)
              key         = 'event_hook_1', #Non-Anonomous key for replacing this function. Required if anon, not anon recorded as module + funcname
              anon        = False,          #If a hook is bound to a namespace or not for replacing it
              mode        = 'post',         #Timing of function (cache, pre, post, wrap, context)
              see_args    = False,          #See args & kwargs or not, default = False
              passthrough = True,)          #If the values will be passed through, which allows for inline changes pre and post.
        def add_c_to_res(self,result):
            return result + add_me.get()
        
        @hook(event = 'event_1',
            #   key   = 'event_hook_2',     #If anon, this *cannot* be overriden by inheritance 
              mode  = 'context')            #Runs as a context_manager. 
        def run_with_c_as_3(self):
            t = add_me.set(3)
            yield                           #Can yield values of args,kwargs if passthrough=True
            add_me.reset(t)
    
    class base(mixin, Hookable):
        
        @hooked(event = 'event_1')
        def func(self,value:int):
            return value
        
    assert 4 == base().func(1)