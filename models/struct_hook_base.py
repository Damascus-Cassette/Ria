''' 
Inherited hooking merge system, based on namespace of contained func by default. 

All hooked funcs must be called with the instance|cls w/a. 
run_hooks provides a header to do so

Masking applies based on expected input: 
    instance hooks will not be called when run_hooks is provided a class 

'@run_with_hooks' wrapper was removed from this version for the complexity required in setup in __init__
'''

from typing  import Callable, Self
from inspect import isclass
from types   import LambdaType
from typing  import Annotated

class _hook():
    ''' Intermediate object that gets replaced on inheritance.
    All hooks are run through this class, and all calls must contain arg of instance '''
    
    func            : Annotated[Callable , "Function To call"]
    name            : Annotated[str      , "Function Name, for unique Namespace"]
    req_unique_name : Annotated[bool     , "If unique Namespace is required"]
    key             : Annotated[str      , "EventKey to call contained func on"]
    method_type     : Annotated[str      , "Define first arg of called func, must be in 'inst','cls','static'"]

    def __init__(self, func, key, method_type:str = 'inst', req_unique_name:bool = True):
        ''' Key is eventkey '''
        assert method_type in ['inst','cls','static']

        self.func = func

        print('REQ UNIQUE TYPE:',req_unique_name)
        
        self.req_unique_name = req_unique_name
        # if isinstance(func,LambdaType):
        #     self.req_unique_name = False

        self.method_type = method_type
        self.name = func.__name__
        self.key  = key

    def __call__(self, *args, **kwargs):
        self.func(*args,**kwargs)
    
    def __repr__(self):
        s_id = super().__repr__().strip('<>')
        s_event = self.key
        s_name = self.name
        f_id = self.func.__repr__()
        f_name = self.func.__name__
        req_uid = self.req_unique_name
        # return f'< {s_id} : {f_id} >'
        return f'< HOOK | Event: {s_event} | Name:{s_name} | req_uid:{req_uid} | function: {f_id} >'
    
def hook(func:Callable|str=None,/,*,key=None, method_type:str='inst', req_unique_name:bool=True):
    if callable(func):
        if not key:
            key = func.__name__
        return _hook(func,key,method_type,req_unique_name)
    
    elif key:
        def _create_hook(func):
            return _hook(func,key,method_type,req_unique_name)
        return _create_hook

    else:
        def _create_hook(func):
            key = func.__name__
            return _hook(func,key,method_type,req_unique_name)
        return _create_hook


class hook_dict(dict):
    ''' dict w/default of list[hook]. Union produces new inst w/ unique required joined namespace. '''

    data : list[hook]

    def __missing__(s,k)->list[hook]:
        ret = s[k] = []
        return ret
    
    def __or__(s,o) -> Self:
        '''Union to new instance with filtering by req_unique_name (dont add to filter list when false)'''

        new = hook_dict()
        filter_list = hook_dict()

        for k,v in s.items():
            for x in v:
                if x.name in filter_list[k] and x.req_unique_name:
                    continue
                
                new[k].append(x)

                if x.req_unique_name:
                    filter_list[k].append(x.name)
        
        for k,v in o.items():
            for x in v:
                if x.name in filter_list[k] and x.req_unique_name:
                    continue
                
                new[k].append(x)

                if x.req_unique_name:
                    filter_list[k].append(x.name)

        return new
    
    def run_hooks(self,key,container=None,*args,**kwargs):
        if not isclass(container):
            self.run_inst_hooks(key,container,*args,**kwargs)
        self.run_cls_hooks(key,container,*args,**kwargs)
        self.run_static_hooks(key,*args,**kwargs)
    
    def run_static_hooks(self,key,*args,**kwargs):
        for x in self[key]:
            if x.method_type == 'static':
                x(*args,**kwargs)

    def run_inst_hooks(self,key,cont,*args,**kwargs):
        for x in self[key]:
            if x.method_type == 'inst':
                x(cont,*args,**kwargs)

    def run_cls_hooks(self,key,cont,*args,**kwargs):
        if not isclass(cont):
            cont = cont.__class__

        for x in self[key]:
            if x.method_type == 'cls':
                x(*args,**kwargs)
        

class Hookable():
    _hooks : hook_dict

    def run_hooks(self,key:str,*args,**kwargs):
        self._hooks.run_hooks(self,key,*args,**kwargs)

    def __init_subclass__(cls):
        hooks = hook_dict()

        for k,v in vars(cls).items():
            if isinstance(v,_hook):
                hooks[v.key].append(v)

        if not isinstance(getattr(cls,'_hooks',None),(hook_dict,dict)):
            cls._hooks = hooks
        else:
            cls._hooks = getattr(cls,'_hooks')|hooks


if __name__ == '__main__':
    from pprint import pprint
    class a(Hookable):
        
        @hook(key = 'event1')
        def func1():
            ...            
        @hook(req_unique_name=False)
        def func2():
            ...
    
    class b(a):
        @hook(key = 'event1')
        def func1():
            ...
        @hook
        def func2():
            ...
    
    pprint(b._hooks)
    assert len(b._hooks['event1']) == 1
    assert len(b._hooks['func2']) == 2