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
    def __init__(self,generator):
        self.generator = generator
    def __enter__(self):
        return next(self.generator)
    def __exit__(self,*args,**kwargs):
        # StopIteration
        try:
            next(self.generator)
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

class _event(_shared_class):...

class _hook(_shared_class):
    def __init__(self ,
                func        :FunctionType|Self ,
                /,
                event       :str               ,
                *,
                key         :str    = None     ,
                anon        :bool   = None     ,
                mode        :str    = None     ,
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
        #Modes must be uniform, inherit if none and raise if different in chain.
        self.func        = func
        self.event       = event
        self.key         = key  if  key          else (func.__module__ + func.__name__)
        self.anon        = anon if (key or anon) else (True)
        self.mode        = mode
        self.see_args    = see_args
        self.passthrough = passthrough
        if passthrough and not see_args: 
            raise Exception('HOOK SYSTEM: Passthrough must have see_args enabled') 
        
        _modes = list(set([x.mode for x in self.hook_siblings if x.mode is not None]))
        if len(_modes)>1:
            raise Exception('HOOK SYSTEM: hook chain modes are not uniformly!')
        elif len(_modes)==1:
            for x in self.hook_siblings:
                x.mode = _modes[0]

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

    def run(self,*args,**kwargs):
        assert self.mode is not None
        assert self.mode != 'context'

        if self.see_args and (self.passthrough or self.mode == 'wrap'):
            res =  self.func(*args,**kwargs)
            assert res is not None
            return res
        elif self.see_args:
            self.func(*args,**kwargs)
            return args,kwargs
        else: 
            self.func()
        
    def return_context_generator_object(self,*args,**kwargs):
        return _enter_exit_hidden(self.func(*args,**kwargs))
    
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

    def __call__(self,container,*args,**kwargs):
        #May require __get__ with functools.partial to get container iirc
        #header is called, not a middle stack item.
        # container : Hookable = args[0]
        return container._hooks.run_with_hooks(self,container,self.func,args,kwargs)
    
    def __get__(self,instance,owner):
        if instance is None:
            return self
        return partial(self.__call__,instance)

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

from functools import partial
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
        new = _def_dict()
        for k,v in (other.hooked | self.hooked).items():
            new[k]=v
        self.hooked = new
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
        for hook   in obj.hook_siblings:   self.intake_hook(hook)
        for hooked in obj.hooked_siblings: self.intake_hooked(hooked)
    
    def intake_hook(self,hook):
        if not hook.anon: 
            ls = self.anon_hooks[hook.event]
            if hook not in ls: 
                print('APPENDED HOOK TO ANON')
                ls.append(hook)
            return
        print('APPENDED HOOK TO NAMED')
        self.named_hooks[hook.event][hook.key] = hook
        
    def intake_hooked(self,hooked):
        ls = self.hooked[hooked.event]
        if hooked not in ls: 
            ls.append(hook)
            print('ADDED TO HOOKED')
    
    def run_with_hooks(self, hooked_inst:_hooked, container, func, args, kwargs):
        ''' Run a hooked function, runs with the hooks ascociated (also runs events on obj) '''
        #Run hooked, run hooks, post events, then exit context
        with _validate_op_chain(container,hooked_inst.event):
            hooks = copy(self.anon_hooks[hooked_inst.event])
            hooks.extend(list(self.named_hooks[hooked_inst.event].values()))
                #Retrieve hooks
            events = hooked_inst.event_siblings
                #Retrieve events

            cache,pre,post,wrap,context = self.split_hooks_to_modes(hooks)
                #split hooks

            for x in cache:
                #TODO: how should cache retrieval interact with events?
                res = x.run(container, *args, **kwargs)
                if res is not _unset:
                    return res

            _context = []
            for x in context:
                gen = x.return_context_generator_object(*args,**kwargs)
                if x.passthrough:
                    args,kwargs = gen.__enter__()
                else:
                    gen.__enter__()
                _context.append(gen)

            for x in pre:
                args,kwargs = x.run(container, *args,**kwargs)
            
            func = hooked_inst.func
            for x in wrap:
                func = x.run(container, func,*args,*kwargs)
                assert isinstance(func,FunctionType)
            
            res = func(container,*args,**kwargs)

            for x in post:
                res = x.run(container, res)

            for x in events:
                x.post(container, hooked_inst.event, func, args, kwargs, res)

            for x in _context[-1:]:
                x.__exit__()

        return res

    def run_as_hook(self, hook_inst:_hook, args, kwargs):
        ''' Hooks are run without triggering hooked atm, Limits the possiblity of recursion '''
        # ''' Runs a function via it's hook (also runs events on obj & calls hooked w/a + throw error with recursive event triggering) '''
        #TODO: Maybe run downstream hooked and post events?

        return hook_inst.func(*args,**kwargs)

    
    def split_hooks_to_modes(self,hooks)->tuple[list[_hook]]:
        items = _def_dict()
        for x in hooks:
            items[x.mode].append(x)
        return items['cache'],items['pre'], items['post'], items['wrap'], items['context']
        

class Hookable():
    _hooks : hook_group
    def __init_subclass__(cls):
        ''' Create new hooks, integrate local with inherited or create from nothing if not here'''

        hg = hook_group()
        if (a:=getattr(cls, '_hooks',None)) is not None:
            hg.merge_in(a)
        cls._hooks = hg

        # for k,v in cls.__dict__.items():
        for k,v in vars(cls).items():
            print(k,v)
            if isinstance(v,(_hook,_hooked,_event)):
                hg.intake(v)

# def event_post():...
# def event_subscribe():...

from contextvars import ContextVar
if __name__ == '__main__':

    add_me = ContextVar('addme',default=1)
    class mixin(Hookable):

        @hook(event       = 'event_1',      #Hook event name. (Despite 'event' term this is always local to object)
              key         = 'event_hook_1', #Non-Anonomous key for replacing this function. Required if anon, not anon recorded as module + funcname
              anon        = False,          #If a hook is bound to a namespace or not for replacing it
              mode        = 'post',         #Timing of function (cache, pre, post, wrap, context)
              see_args    = True,           #See args & kwargs or not, default = False
              passthrough = True,)          #If the values will be passed through, which allows for inline changes pre and post.
        def add_c_to_res(self,result):
            print('CALLED ME')
            return result + add_me.get()
        
        @hook(event = 'event_1',
            #   key   = 'event_hook_2',     #If anon, this *cannot* be overriden by inheritance 
              mode  = 'context')            #Runs as a context_manager. 
        def run_with_c_as_3(self):
            t = add_me.set(3)
            yield                           #Can yield values of args,kwargs if passthrough=True
            add_me.reset(t)
    
    class base(mixin,Hookable):
        
        # @event(event ='postmarker', )
        @hooked(event = 'event_1')
        def func(self,value:int=None):
            return value
        
    from pprint import pprint
 
    pprint(base._hooks.anon_hooks)
    pprint(base._hooks.named_hooks)
    pprint(base._hooks.hooked)

    b = base()
    print (base.func.__class__) 
    # print (b.func.__class__) 
    assert isinstance(base.func,_hooked) 
    result = b.func(1)
    print(result)
    assert 4 == result