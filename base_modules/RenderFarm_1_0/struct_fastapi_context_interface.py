from contextvars import ContextVar
from types       import FunctionType
from enum        import Enum


class MODES(Enum):
    LOCAL   = 1
    WORKER  = 2
    MANAGER = 3


mode = ContextVar('prgm_instance_mode', default = MODES.LOCAL)

class _io():
    _lc_func        : FunctionType
    _mg_func        : FunctionType
    _wk_func        : FunctionType
    _mg_local_func  : FunctionType
    _wk_local_func  : FunctionType

    def __init__(self, func, in_manager=False, in_worker=False):
        ''' Assumption that the first func is local '''
        self._local_func = func
        self._local_func_in_manager = in_manager
        self._local_func_in_worker  = in_worker

    def manager(self,*fastapi_args, see_con = False, **fastapi_kwargs):
        def wrapper(func):
            self._mg_func = func
            func_wrapped = self._wrap_manager(fastapi_args=fastapi_args, see_con = see_con, fastapi_kwargs=fastapi_kwargs)
            return func_wrapped
        return wrapper
    
    def worker(self,*fastapi_args, see_con = False, **fastapi_kwargs):
        def wrapper(func):
            self._wk_func = func
            func_wrapped = self._wrap_worker(fastapi_args=fastapi_args, see_con = see_con, fastapi_kwargs=fastapi_kwargs)
            return func_wrapped
        return wrapper
    
    def manager_local(self): #(mg).func() Calls this when
        def wrapper(func):
            self._mg_local_func = func
            return None
        return wrapper 

    def worker_local(self):
        def wrapper(func):
            self._wk_local_func = func
            return None
        return wrapper 

    def __call__(self,*args,**kwargs):
        ''' Check con_target (assume responce if not None) '''
        mode = mode.get()
        if mode is  MODES.LOCAL:
            return self._lc_func(*args,**kwargs)
        if con_target.get() is None:
            match mode:
                case MODES.WORKER:
                    ...
                case MODES.MANAGER:
                    ...
        else:
            match mode(), :
                case 
    
    
        ...

    def __get__():
        #with, yield partial below??
        ...

    def mg(self, *args, _inst=None, _con=None,_rep=None, **kwargs):
        ''' contextually set connection or call locally, if _con, _rep are not set otherwise '''
    def wk(self, *args, _inst=None, _con=None,_rep=None, **kwargs):
        ''' contextually set connection or call locally, if _con, _rep are not set otherwise '''
    def lc(self, *args, _inst=None, _con=None,_rep=None, **kwargs):
        ''' contextually set connection or call locally, if _con, _rep are not set otherwise '''

def io():
    ...