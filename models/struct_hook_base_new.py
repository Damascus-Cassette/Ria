'''A new iteration of the hook module that includes allowences in structure for the planned event system 
Clarity on terms within this project:
Hooks:   object's internal pre and post processors
Events:  Pre-Post event posting to a global list, directional
'''

from typing      import Any,Self
from types       import FunctionType
from functools   import wraps
from contextvars import ContextVar
from contextlib  import contextmanager
from copy import copy

from inspect import isgeneratorfunction

class _enter_exit_hidden():
    def __init__(self,factory):
        self.factory = factory
    def __enter__(self):
        self.first_value =  next(self.factory)
        return self.first_value
    def __exit__(self,*args,**kwargs):
        # StopIteration
        try:
            next(self.factory)
        except StopIteration :
            pass
        except: 
            raise
        return None

_operation_chain = ContextVar('hook_op_chain', default=tuple())
@contextmanager
def _validate_op_chain(item,hook_event_key):
    tp = _operation_chain.get()
    if (item,hook_event_key) in tp:
        raise RecursionError(f'HOOK SYSTEM: Recursion caught: {(item, hook_event_key)}')
    tp += ((item,hook_event_key),)
    t = _operation_chain.set(tp)
    yield
    t = _operation_chain.set(tp)

class _unset():...

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
        if issubclass(func.__class__,_shared_class):
            self.hook_siblings   = func.hook_siblings  
            self.event_siblings  = func.event_siblings 
            self.hooked_siblings = func.hooked_siblings
            func = func.func
        else:
            self.hook_siblings   = []
            self.event_siblings  = []
            self.hooked_siblings = []
        self.hook_siblings.append(self)
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

    def __enter__(self,):
        ...
    def __exit__():
        ...

class _hooked(_shared_class):
    def __init__(self,
                 func:FunctionType|Self ,
                 event:str              ,
                 ):
        if issubclass(func.__class__,_shared_class):
            self.hook_siblings   = func.hook_siblings   
            self.event_siblings  = func.event_siblings  
            self.hooked_siblings = func.hooked_siblings 
            func = func.func
        else:
            self.hook_siblings   = []
            self.event_siblings  = []
            self.hooked_siblings = []
        self.hooked_siblings.append(self)
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

class _def_dict(dict):
    def __missing__(self,key):
        ls = []
        self[key] = ls
        return ls
class _def_dict_dict(dict):
    def __missing__(self,key):
        ls = {}
        self[key] = ls
        return ls

class hook_group():
    ''' Namespace and Anon merging on inheritance via a construction function, plus execution of hooks '''
    
    anon_hooks   : _def_dict[list[hook]]
    named_funcs  : dict[str, _shared_class]
    hooked       : _def_dict[list]

    def __init__(self):
        self.hooked       = _def_dict()
            #Current object state determines all hooked
        self.named_hooks  = _def_dict_dict()
            #Inherited but overridable hooks via a key.
            #Single hook per key
        self.anon_hooks   = _def_dict()
            #cross-inheritance hooks, only added to.

    def merge_in(self,other:Self):
        self.hooked      = other.hooked | self.hooked
        # self.named_hooks = other.named_hooks | self.named_hooks 
    
        for k,v in other.named_hooks.items():
            self.named_hooks[k] = v | self.named_hooks[k] 

        for k,v in other.anon_hooks.items():
            #Unknown: run parent hooks or subclass hooks first?
            self.anon_hooks[k].extend( [x for x in v if not x in self.anon_hooks[k]] ) 
            # ls = [x for x in v if not x in self.anon_hooks[k]]
            # ls.extend(self.anon_hooks[k])
            # self.anon_hooks[k] = ls

    def intake(self,obj:_hook|_hooked):
        ''' Views any _hook,_hooked,_event object and determines if already inside and if anon vs not anon. Adds if does have '''
        for hook   in obj.hook_siblings:   self.intake_hook
        for hooked in obj.hooked_siblings: self.intake_hooked
    
    def intake_hook(self,hook):
        if not hook.anon: 
            ls = self.anon_hooks[hook.event]
            if hook not in ls: 
                ls.append(hook)
            return
        self.named_hooks[hook.event][hook.key] = hook
        
    def intake_hooked(self,hooked):
        ls = self.hooked[hooked.event]
        if hook not in ls: 
            ls.append(hook)
    
    def run_with_hooks(self, hooked_inst:_hooked, container, func, args, kwargs):
        ''' Run a hooked function, runs with the hooks ascociated (also runs events on obj) '''
        #Run hooked, run hooks, post events, then exit context
        with _validate_op_chain(container,hooked_inst.event):
            hooks = copy(self.anon_hooks[hooked.event])
            hooks.append(*self.named_hooks[hooked.event].values())
                #Retrieve hooks
            events = hooked_inst.event_siblings
                #Retrieve events

            cache,pre,post,wrap,context = self.split_hooks_to_modes(hooks)
                #split hooks

            for x in cache:
                #TODO: how should cache retrieval interact with events?
                res = x.run(args,kwargs)
                if res is not _unset:
                    return res

            _context = []
            for x in context:
                gen = x.return_context(*args,**kwargs)
                args,kwargs = gen.__enter__()
                _context.append(gen)

            for x in pre:
                args,kwargs = x.run(args,kwargs)
            
            func = hooked_inst.func
            for x in wrap:
                func = x.run(func,*args,*kwargs)
                assert isinstance(func,FunctionType)
            
            res = func(*args,**kwargs)

            for x in post:
                res = x.run(res)

            for x in events:
                x.run()

            for x in _context[-1:]:
                x.__exit__()

        return res

        #TODO

    def run_as_hook(self, hook_inst:_hook, container, func, args, kwargs):
        ''' Runs a function via it's hook (also runs events on obj & calls hooked w/a + throw error with recursive event triggering) '''
        #Run hook's func, run hooked, post events, then return
        #TODO
    
    def split_hooks_to_modes(self,hooks)->tuple[list[_hook]]:
        items = _def_dict()
        for x in hooks:
            items[x.mode].append(x)
        return items['pre'], items['post'], items['wrap'], items['context']
        

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