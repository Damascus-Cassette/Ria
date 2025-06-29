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

class repo_base():
    context   : Any
    c_engine  : ContextVar
    c_session : ContextVar

    base = None #used later

    @transaction
    def test(cls,c_attr):
        print(getattr(cls.context,c_attr).get())
        #DO something in the db in session context

class settings_standin():    
    def __enter__(self):
        yield self
    def __exit__(self):
        yield self

class db_interface():

    repo    : repo_base
    context : Any

    def __init__(self,settings):

        for k,v in settings.items():        #standin for setting items
            setattr(self,k,v)

        class context:
            ''' Constructed generic context var container. Consider as dict '''
            c_test    = ContextVar('test'    , default = None)

        self.context = context
        self.c_engine  = ContextVar('engine' , default = None)
        self.c_session = ContextVar('session', default = None)

        session_manager = self._session_cm()

        self.repo = type('repo_base', tuple([repo_base]) , { 'c_engine':self.c_engine, 'c_session':self.c_session, 'context':context})
        _transaction.rewrap(self.repo,session_manager)

    def _generic_cm(self,**cust_cvars):

        @contextmanager
        def context_manager(*args,**kwargs):
            cust_tokens = {}
            try:
                for k,v in cust_cvars.items():
                    if isinstance((cvar:=getattr(self.context,k,None)),ContextVar):
                        cust_tokens[k] = cvar.set(v)
                yield
            except:
                raise
            finally:
                for k,v in cust_tokens.items():
                    cvar = getattr(self.context,k)
                    cvar.reset(v)

        return context_manager
        

    def _session_cm(self):
        @contextmanager
        def session_manager(*args,**kwargs):
            try:
                t1 = self.c_engine.set('c_engine_something') 
                t2 = self.c_session.set('c_session_something')
                yield 
            except:
                raise
            finally:
                self.c_engine.reset(t1)
                self.c_session.reset(t2) 
        return session_manager

dbi = db_interface({})

# dbi.repo.make()

with dbi._generic_cm(c_test = 'customMessage')():
    dbi.repo.test('c_test')
    