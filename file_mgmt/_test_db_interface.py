from typing      import Any,TypeAlias,get_type_hints
from contextlib  import contextmanager
from contextvars import ContextVar
from functools   import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .settings import settings_interface

from .db_struct import User,Base


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
                return func(housing_class,*args,**kwargs)
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
        session = cls.c_session.get()
        if not data:
            data = {}
        data = data|kwargs
        
        obj = cls.base()        

        for k,v in data.items():
            assert hasattr(obj,k)
            setattr(obj,k,v)

        session.add(obj)
        # session.flush()
        session.refresh(obj)

        return obj

    @transaction
    def update(cls,obj:base,data=None,**kwargs)->base:
        session = cls.c_session.get()

        if not data:
            data = {}
        data = data|kwargs

        for k,v in data.items(): 
            assert hasattr(obj,k)
            setattr(obj,k,v)

        session.refresh(obj)
        # session.flush()
        
        return obj
    
    @transaction
    def delete(cls,obj)->None:
        session = cls.c_session.get()
        session.delete(obj)
        session.refresh()
        # session.flush()

    @classmethod
    def echo_context(cls,c_attr)->str:
        return getattr(cls.context,c_attr,None).get()

class user_repo(repo_interface_base):
    base = User


class db_interface():
    _repo_base : repo_interface_base
    user_repo  : user_repo 

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
        Base.metadata.create_all(self.engine)

        return self.c_engine.set(self.engine)
    

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
        if not getattr(self,'engine',None):
            self._load_db()

        if not self.c_session.get():
            ## May have to strip this context value if I'm to close the session
            self.c_session.set(Session(bind=self.engine, expire_on_commit = True))

        session        = self.c_session.get()
        in_transaction = session.in_transaction()

        try:
            if in_transaction:
                _session = session.begin_nested()
                t2 = self.c_session.set(_session)
                yield _session
                _session.commit()
            else:
                yield session
                session.commit()
                # session.close()
        except:
            if in_transaction:
                _session.rollback() 
            else:
                session.rollback()  
                session.close()
            raise

        finally:
            if in_transaction:
                self.c_session.reset(t2) 
