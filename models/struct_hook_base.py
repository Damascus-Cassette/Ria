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
from copy        import copy
from functools   import partial

# from inspect import isgeneratorfunction

######## UTILITIES ########
#region
class _unset():...
class _shared_class():...

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
    _operation_chain.reset(t)

#endregion


######## HOOKS INDV ########
#region

class _hook(_shared_class):
    def __init__(self ,
                func        :FunctionType|Self ,
                /,
                event       :str               ,
                *,
                key         :str    = None     ,
                mode        :str    = None     ,
                anon        :bool   = None     ,
                see_args    :bool   = True     ,
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
        self.hook_siblings.insert(0,self)
        #Modes must be uniform, inherit if none and raise if different in chain.
        self.func        = func
        self.event       = event
        # print('SELF EVENT:', self.event)
        self.key         = key  if  key          else (func.__module__ + func.__name__)
        self.anon        = anon if (key or (anon is not None)) else (True)
        self.mode        = mode 
        self.see_args    = see_args
        self.passthrough = passthrough
        if passthrough and not see_args: 
            raise Exception('HOOK SYSTEM: Passthrough must have see_args enabled') 
        
        _modes = list(set([x.mode for x in self.hook_siblings if x.mode is not None]))
        if len(_modes)>1:
            raise Exception('HOOK SYSTEM: hook chain modes must be uniform!')
        elif len(_modes)==1:
            for x in self.hook_siblings:
                x.mode = _modes[0]

    def __call__(self, container, *args, **kwargs):
        return container._hooks.run_as_hook(self,container,args,kwargs)


    @classmethod
    def wrapper(cls,
                /,
                event       :str               ,
                *,
                key         :str    = None     ,
                anon        :bool   = None     ,
                mode        :str    = None     ,
                see_args    :bool   = True     ,
                passthrough :bool   = None     ,
                )->Self:
        ''' Produce a hook object
        :param event:       event label, called on any self hooked funcs where event's are the same 
        :param key:         When decalared, a non-anon function that is replaced by the next hook uses this key
        :param anon:        A function that is floating and cannot be overridden
        :param mode:        in ['pre','post','cache','wrap','context'], determines when & how the hook function is called. Must be the same for a hook stack
        :param see_args:    if the function is passed in the arguments
        :param passthrough: if the function's output replaces the input (Mode dependant and requires see_args)
        :returns: Configured Hook Instance, Nestable
        :rtype:   _hook
        '''

        def wrapper(func):
            # print('CREATING HOOK OF,',func, event)
            return (cls(func,
            # return wraps(func)(cls(func,      #Wraps was causing a collission when run multiple times on the same func!
                event       = event       ,
                key         = key         ,
                anon        = anon        ,
                mode        = mode        ,
                see_args    = see_args    ,
                passthrough = passthrough ))
        return wrapper

    def run(self,container,*args,**kwargs):
        assert self.mode is not None
        assert self.mode != 'context'

        if self.see_args and (self.passthrough or self.mode == 'wrap'):
            res =  self.func(container,*args,**kwargs)
            assert res is not None
            return res
        elif self.see_args:
            self.func(container,*args,**kwargs)
            return args,kwargs
        else: 
            self.func()
        
    def return_context_generator_object(self,container,*args,**kwargs):
        return _enter_exit_hidden(self.func(container,*args,**kwargs))
    
    def __repr__(self):
        return f'< Hook Obj: ({self.event} -> {self.__module__}.{self.func.__qualname__}) at {id(self)} >'

hook         = _hook  .wrapper
#endregion


######## HOOKS TRIGGERS ########
#region

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
        self.hooked_siblings.insert(0,self)
        self.func  = func
        self.event = event

    def __call__(self,container,*args,**kwargs):
        if not hasattr(container,'_hooks'):
            # raise Exception(container.__class__.mro())
            # raise Exception(container.__class__.__bases__)
            raise Exception(hasattr(container,'__hooks_initialize__'))
            
            print(vars(container))
            raise Exception('')
            ...
        return container._hooks.run_with_hooks(self,container,self.func,args,kwargs)
    
    def __get__(self,instance,owner):
        if instance is None:
            return self
        return partial(self.__call__,instance)

    @classmethod
    def wrapper(cls       ,
                event:str ,
                )->Self:
        ''' Returns a _hooked object that executes the wrapped function with relevent object-local hooks
        :param event: Event key, runs all relevent hooks 
        :returns: wrapper for hook, nestable
        :rtype: _hooked
        '''
        def wrapper(func):
 
            # return wraps(func)(cls(func,event)) #Wraps was causing a collission when run multiple times on the same func!
            return cls(func = func,
                    event = event)
        return wrapper

hook_trigger = _hooked.wrapper
#endregion


######## EVENT TRIGGERS ########
#region
class _event_sub(_shared_class):    ...
class _event_trigger(_shared_class):...
def event_sub(*args,**kwargs):
    def func(func): 
        return func
    return func
def event_trigger(*args,**kwargs):
    def func(func): 
        return func
    return func

#endregion


######## HOOKS COLLECTION ########
#region

class hook_group():
    ''' Namespace and Anon merging on inheritance via a construction function, plus execution of hooks '''
    
    anon_hooks   : _def_dict[list[hook]]
    named_funcs  : dict[str, _shared_class]
    hooked       : _def_dict[list]

    Allowed_Modes = ('pre','post','cache','wrap','context')

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
    
        for k,v in other.named_hooks.items():
            self.named_hooks[k] = v | self.named_hooks[k] 

        for k,v in other.anon_hooks.items():
            #Unknown: run parent hooks or subclass hooks first?
            self.anon_hooks[k].extend( [x for x in v if not x in self.anon_hooks[k]] ) 


    def intake(self,obj:_hook|_hooked):
        ''' Views any _hook,_hooked,_event object and determines if already inside and if anon vs not anon. Adds if does have '''
        assert (obj in obj.hook_siblings) or (obj in obj.hooked_siblings) or (obj in obj.event_siblings)
        for hook_inst   in obj.hook_siblings:   self.intake_hook(hook_inst)
        for hooked_inst in obj.hooked_siblings: self.intake_hooked(hooked_inst)
        # for event_inst  in obj.event_siblings:  self.intake_event(event_inst)
    
    def intake_hook(self,hook_inst):
        assert hook_inst.mode in self.Allowed_Modes
        if hook_inst.anon: 
            ls = self.anon_hooks[hook_inst.event]
            if hook_inst not in ls: 
                ls.append(hook_inst)
            # print('INTAKING ANON',hook_inst)
            return
        # print('INTAKING',hook_inst)
        self.named_hooks[hook_inst.event][hook_inst.key] = hook_inst
        
    def intake_hooked(self,hooked_inst):
        ls = self.hooked[hooked_inst.event]
        if hooked_inst not in ls: 
            ls.append(hook)
    
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
                if x.see_args:
                    gen = x.return_context_generator_object(container,*args,**kwargs)
                else:
                    gen = x.return_context_generator_object(container)

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
            # res = func(container,*args,**kwargs)

            for x in post:
                res = x.run(container, res)

            for x in events:
                x.post(container, hooked_inst.event, func, args, kwargs, res)

            for x in _context[-1:]:
                x.__exit__()

        return res

    def run_as_hook(self, hook_inst:_hook, *args, **kwargs):
        ''' Hooks are run without triggering hooked atm, Limits the possiblity of recursion '''
        #TODO: Maybe run sibling_hooked and sibling_events?

        return hook_inst.func(*args,**kwargs)

    
    def split_hooks_to_modes(self,hooks)->tuple[list[_hook]]:
        items = _def_dict()
        for x in hooks:
            items[x.mode].append(x)
        return items['cache'],items['pre'], items['post'], items['wrap'], items['context']
        
class Hookable():
    ''' Mixin class for enabling hooks on all classes, must also be on class mixing into new cls '''
    _hooks : hook_group

    def __init_subclass__(cls):
        ''' Create new hooks, integrate local with inherited or create from nothing if not here'''
        cls.__hooks_initialize__()
        super().__init_subclass__()

    @classmethod
    def __hooks_initialize__(cls):
        if '_hook' in cls.__dict__.keys():
            hg = cls._hook
        else: 
            hg = hook_group()
        
        parent_hooks = ((getattr(x,'_hooks'),cls) for x in cls.__bases__ if hasattr(x,'_hooks'))
        for x,c in parent_hooks:
            # if not 'socket' in c.__name__ and not 'S_GROUP' in c.__name__:
            #     print('MERGING IN _HOOK ONTO', c.__name__)
            hg.merge_in(x)
            if getattr(cls,'_hook_debug_temp_loud_',False):
                print(f'MERGING HOOKS IN {cls.__qualname__} <==',x)

        # if (a:=getattr(cls, '_hooks',None)) is not None:
        #     hg.merge_in(a)
        cls._hooks = hg

        for k in dir(cls):
            v = getattr(cls,k)
            if getattr(cls,'_hook_debug_temp_loud_',False):
                print(k,' : ',v)
            if isinstance(v,(_hook,_hooked,_event_sub,_event_trigger)):
                hg.intake(v)
                print('INTOOK', k)

#endregion


######## LOCAL TESTING ########
#region


if __name__ == '__main__':
    from contextvars import ContextVar

    add_me = ContextVar('addme',default=1)
    class _test():
        def __init_subclass__(cls):
            ...
            # return super().__init_subclass__()
    class mixin(Hookable,_test):

        @hook(event       = 'event_1',      #Hook event name. (Despite 'event' term this is always local to object)
              key         = 'event_hook_1', #Non-Anonomous key for replacing this function. Required if anon, not anon recorded as module + funcname
              anon        = False,          #If a hook is bound to a namespace or not for replacing it, auto True if key presented.
              mode        = 'post',         #Timing of function (cache, pre, post, wrap, context)
            #   see_args    = True,           #See args & kwargs or not, default = True
              passthrough = True,)          #If the values will be passed through, which allows for inline changes pre and post.
        def add_c_to_res(self,result):
            return result + add_me.get()
        
        @hook(event='event_1', mode='context', see_args=False)            
        @hook(event='event_2', mode='context', see_args=False)
        def run_with_c_as_3(self):
            t = add_me.set(3)
            yield              #Can yield values of args,kwargs if passthrough=True
            add_me.reset(t)

        @hook(event = 'event_1' , mode = 'pre')
        def run_pre(self,arg):
            assert arg == 1

        @hook_trigger(event = 'event_2')
        def func2(self):
            assert add_me.get() == 3 

    class base(mixin,Hookable):
        
        # @event_subscriber(event ='postmarker', )
        # @event_publisher(event ='postmarker', )
        @hook_trigger(event = 'event_1')
        def func(self,value:int=None,):
            return value
        
        # run_with_c_as_3 = hook(event = 'event_2', mode  = 'context')(mixin.run_with_c_as_3)
            #This method can add hooks to inherited functions, though it's kinda jank

        @hook(event = 'cache_test', mode = 'cache', passthrough = True)
        def _func3(self, value:str):
            if value == 'a': return 'AA'
            else:            return _unset

        @hook_trigger(event = 'cache_test')
        def func3(self,value:str):
            assert value != 'a'
            return value.capitalize()
             

    from pprint import pprint
    # pprint(('Anon  Hooks:', base._hooks.anon_hooks ))
    # pprint(('Named Hooks:', base._hooks.named_hooks))
    # pprint(('Hooked:', base._hooks.hooked))

    b = base()
    assert isinstance(base.func,_hooked) 
    assert 4 == b.func(1)
    b.func2()

    assert 'AA' == b.func3('a')
    assert 'B' == b.func3('b')

#endregion
