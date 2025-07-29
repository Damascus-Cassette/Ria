import functools
from typing import Callable
from contextvars import ContextVar

#decorater class
class _lazy:
    def __init__(self, func,):
        self.func = func

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)

    def __call__(self, *args, **kwargs):
        return self.func(*args, *kwargs).upper()

def lazy(func:Callable|ContextVar):
    #Make relative with allowence of self.attr instead of context var. 
    #This would allow for a property to walk to see if any have been invalidated/changed to re-call the lazy value (in which lazy can be anything)
    if callable(func) and not isinstance(func,ContextVar):
        force = func
        def make_lazy(func):
            _lazy(func,force)
    else:
        raise Exception('Force value must be provided!')
 

force_lazy = ContextVar(default=True)

#normal class
class base_string:
    def __init__(self, base):
        self.base = base

    @lazy(force_lazy)
    def get_base_string(self):
        return self.base

s = base_string('word worD')
print(s.get_base_string())