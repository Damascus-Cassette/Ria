from typing      import Any,TypeAlias,get_type_hints
from contextlib  import contextmanager
from contextvars import ContextVar
from functools   import wraps

from sqlalchemy import create_engine

from .settings import settings_interface

class _transaction():
    ''' Placeholder and re-wrap on db_interface init'''

    def __init__(self, func):
        self.func = func
    
    @classmethod
    def rewrap(cls, t_cls, context_func):
        for k in dir(t_cls):
            if isinstance(var := getattr(t_cls,k), cls):
                new_func = cls.makefunc(t_cls,var.func,context_func)
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

    base : TypeAlias = None

    @transaction
    def create(cls,data=None,**kwargs)->base:
        if not data:
            data = {}
        data = data|kwargs
        
        inst = cls.base()

        for k,v in data.items():
            assert hasattr(inst,k)
            setattr(inst,k,v)

        cls.session.add(inst)

        return inst

    @transaction
    def update(cls,obj:base,data=None,**kwargs)->base:
        if not data:
            data = {}
        data = data|kwargs

        for k,v in data.items(): 
            assert hasattr(obj,k)
            setattr(obj,k,v)

        return obj
    
    @transaction
    def delete(cls,obj)->None:
        cls.session.delete(obj)

    @classmethod
    def echo_context(cls,c_attr)->str:
        return getattr(cls.context,c_attr,None).get()



class db_interface():
    _repo_base : repo_interface_base
    context : Any

    def __init__(self,settings:dict|str):

        self.context = self._construct_context({
            'platform':'default',
            })
        self.c_engine  = ContextVar('engine' , default = None)
        self.c_session = ContextVar('session', default = None)
        
        self._load_settings(settings)
        self._load_db()

        self._construct_repos_from_anno()
    
    def _load_settings(self,settings):
        if isinstance(settings,str):
            self.settings = settings_interface(override_context=self.context)
            self.settings.load_file(settings)
        else:
            self.settings = settings_interface(values=settings,override_context=self.context)
        
    def _load_db(self):
        # self.settings.fetch(value-uid)
        db_p = self.settings.database.database_fp
        self.engine = create_engine(db_p)
        self.c_engine.set(self.engine)

        # if not self._db_check_lock(force):
        #     self._db_register_lock(use_atexit=True)
        # else:
        #     raise Exception('')
    # def _db_check_lock(self)->bool:
    #     ''' check if lock apart from current thread exists in database. If so no transaction can complete unless forced '''
    # def _db_register_lock(self,use_atexit)->None:
    #     ''' Register lock, add atexit command for removal of lock'''
    #     import atexit
    # def _db_unregister_lock(self)->None:
    #     ...

    def _construct_repos_from_anno(self):
        for k,th in self.__anno_resolved__.items():
            i = getattr(self,k,None)
            if issubclass(th,repo_interface_base) and not i:
                new_cls = self._construct_repo([th],self.context)
                setattr(self,k,new_cls)

    def _construct_context(self,cvars:dict):
        items = {}
        for k,v in cvars.items():
            items[k] = ContextVar(k,default=v)

        return type('context',tuple([object]),items)

    def _construct_repo(self,base_classes,context):
        session_manager = self.session_cm
        ret = type('repo_base', tuple(base_classes) , {'db_interface':self, 'c_engine':self.c_engine, 'c_session':self.c_session, 'context':context})
        _transaction.rewrap(ret,session_manager)
        return ret

    @property
    def __anno_resolved__(self):
        if not hasattr(self,'__anno_resolved_cache__'):
            self.__anno_resolved_cache__ = get_type_hints(self.__class__)
        return self.__anno_resolved_cache__

    @contextmanager
    def generic_cm(self,**kwargs):
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
    def session_cm(self,*args,**kwargs):
        try:    
            t1 = self.c_engine.set('c_engine_something') 
            t2 = self.c_session.set('c_session_something')
            yield 
        except:
            raise
        finally:
            self.c_engine.reset(t1)
            self.c_session.reset(t2) 
