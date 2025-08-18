from contextvars import ContextVar
from contextlib  import contextmanager
from functools import wraps

class _defaultdict(dict):
    def __missing__(self,key):
        return 0
    

use_print_debug     = ContextVar('use_print_debug'  , default = True)

print_debug_level   = ContextVar('print_debug_level'  , default = 0 )
print_debug_targets = ContextVar('print_debug_targets', default = _defaultdict())
    #Tuple of target func names/ids and the value to set
print_debug_nestedlevel = ContextVar('nested_level',default = 0)
# print_debug_nestedstack = ContextVar('nestedstack', default=tuple())
    #TODO: Add color based on func

from .text_colors import (colors as t_colors,
                          modes  as t_modes )
import copy 
@contextmanager
def debug_level(v):
    t = print_debug_level.set(v)
    yield
    print_debug_level.reset(t)

@contextmanager
def debug_targets(targets:dict):
    v = print_debug_targets.get()
    v = copy.copy(v)
    for k,i in targets.items(): v[k]=i
    t = print_debug_targets.set(v)
    yield
    print_debug_targets.reset(t)


@contextmanager
def nested_level_add1():
    v = print_debug_nestedlevel.get()
    t = print_debug_nestedlevel.set(v+1)
    yield
    print_debug_nestedlevel.reset(t)

def _debug_print(*args,**kwargs):
    print(' | '*print_debug_nestedlevel.get(),*args,**kwargs)

def debug_print(*args, threshold=-1, **kwargs):
    if threshold >= print_debug_level:
        _debug_print(*args,**kwargs)

def _rep(item):
    if (c:=getattr(item,'context',None)) is not None:
        return c.Formatted_Repr
    return str(item)

def _arg_reps(self,args):
    res = []
    for x in args:
        res.append(_rep(x))
    return res
def _kwarg_reps(self,kwargs):
    res = {}
    for k,v in kwargs:
        res[k] = _rep(v)
    return res

import inspect
def debug_print_wrapper(threshold    = 1    ,
                        /,*,
                        group_id     = None,
                        print_pre    = True,
                        print_post   = True, 
                        print_args   = False, 
                        print_result = False,
                        print_color : tuple[float]|str  = None):
    def sub_wrapper(func):
        if use_print_debug.get():
            module_id = (' .'+func.__module__).split('.')[-1]

            @wraps(func)
            def wrapper(*args,**kwargs):

                dbt  = print_debug_targets.get()
                dbl = max([dbt[func.__name__],dbt[group_id],dbt[module_id],print_debug_level.get()])
                #preprint
                if print_pre and (threshold <= dbl):
                    _debug_print(f'RUNNING FUNC {func.__name__} || GROUP: {group_id}')
                    if print_args:  
                        _debug_print(f'{t_modes.DIM[0]}|-> ARGS:   {_arg_reps(args)}{t_modes.DIM[1]}') 
                        _debug_print(f'{t_modes.DIM[0]}|-> KWARGS: {_kwarg_reps(kwargs)}{t_modes.DIM[1]}') 
                
            
                with nested_level_add1():
                    val = func(*args,**kwargs)
            
                #postprint
                if print_post and (threshold <= dbl):
                    _debug_print(f'{t_modes.DIM[0]}|-> FIN FUNC {func.__name__}{t_modes.DIM[1]}')
                    if print_result:  
                        _debug_print(f'{t_modes.DIM[0]}|-> RESULT: {_rep(val)}{t_modes.DIM[1]}') 

                return val
            
            return wrapper
        return func

    return sub_wrapper


# @debug_print_wrapper(1,print_result=True,print_args=True)
# def test_func(a,b=0):
#     print('Regular print inside_func')
#     return a + b

# test_func(1,1)

# @debug_print_wrapper(1,print_result=True,print_args=True)
# def test_func2(a,b,c):
#     v1 = test_func(a,b)
#     v2 = test_func(v1,c)
#     return v2

# with debug_level(2):
#     test_func2(1,1,1)




