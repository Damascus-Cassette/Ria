from contextvars import ContextVar
from contextlib  import contextmanager
from functools   import wraps
from typing      import Any
# from contextlib  import contextmanager

class _transaction():
    ''' Placeholder and re-wrap on db_interface init'''

    def __init__(self, func):
        self.func = func
    
    @classmethod
    def rewrap(cls, t_cls, context_func):
        for k in dir(t_cls):
            if isinstance(var := getattr(t_cls,k), cls):
                new_func = cls.makefunc(t_cls,var.func,context_func)
                print(t_cls, k, new_func)
                setattr(t_cls, k, new_func)

    @staticmethod
    def makefunc(housing_class, func, context_func):
        @wraps(func)
        def new_func(*args,**kwargs):
            with context_func():
                v = func(housing_class,*args,**kwargs)
        return new_func

def transaction[T](func:T)->T:
    return _transaction(func)

class repo_interface_base():
    context   : Any
    c_engine  : ContextVar
    c_session : ContextVar

    base = None #used later

    @transaction
    def test(cls,c_attr=''):
        print(cls.c_engine.get())
        print(cls.c_session.get())
        if c_attr:
            print(getattr(cls.context,c_attr).get())


class db_interface():
    repo    : repo_interface_base
    context : Any

    def __init__(self,settings):

        for k,v in settings.items():        #standin for setting items
            setattr(self,k,v)

        self.context = self._construct_context({
            'c_test':None,
            })
        
        self.c_engine  = ContextVar('engine' , default = None)
        self.c_session = ContextVar('session', default = None)

        self.repo = self._construct_repo([repo_interface_base], self.context)

    def _construct_context(self,cvars:dict):
        
        items = {}
        for k,v in cvars.items():
            items[k] = ContextVar(k,default=v)

        return type('context',tuple([object]),items)

    def _construct_repo(self,base_classes,context):
        session_manager = self._session_cm
        ret = type('repo_base', tuple(base_classes) , {'db_interface':self, 'c_engine':self.c_engine, 'c_session':self.c_session, 'context':context})
        _transaction.rewrap(ret,session_manager)
        return ret

    @contextmanager
    def _generic_cm(self,**kwargs):
        cust_tokens = {}
        try:
            for k,v in kwargs.items():
                if isinstance((cvar:=getattr(self.context,k,None)),ContextVar):
                    cust_tokens[k] = cvar.set(v)
            yield
        except:
            raise
        finally:
            for k,v in cust_tokens.items():
                cvar = getattr(self.context,k)
                cvar.reset(v)

    @contextmanager
    def _session_cm(self,*args,**kwargs):
        try:
            t1 = self.c_engine.set('c_engine_something') 
            t2 = self.c_session.set('c_session_something')
            yield 
        except:
            raise
        finally:
            self.c_engine.reset(t1)
            self.c_session.reset(t2) 

dbi = db_interface({})

dbi.repo.test()

with dbi._generic_cm(c_test = 'customMessage'):
    dbi.repo.test('c_test')
    