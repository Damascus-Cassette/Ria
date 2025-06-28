from .db_struct import (asc_Space_NamedFile, asc_Space_NamedSpace, File, Space, target, Export, Session, User)
import atexit
from sqlalchemy import create_engine

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from .settings import settings_interface

from typing import TypeAlias

c_session = ContextVar('session' , default=None)
c_engine  = ContextVar('engine'  , default=None)


@contextmanager
def _transaction_context_manager(db_interface):
    ''' Temporarly set session & engine within context of execution'''
    c_engine.set (db_interface.get_engine())
    c_session.set(db_interface.get_session()) 

def transaction[F](func:F)->F:
    return _transaction(func)

class _transaction():
    def __init__[F](self, func:F)->F:
        self.func         = func
        self.container = None

    def __call__(self,*args,**kwargs):
        with _transaction_context_manager(self.container.db_interface):
            self.container.db_interface.ensure_c_engine()
            self.container.db_interface.ensure_c_session()

            return self.func(*args,**kwargs)

    @classmethod
    def init_transactions(cls,repo_inst):
        for k,v in repo_inst.__dict__().items():
            if isinstance(v,cls):
                v.container = repo_inst

class repo_baseclass():
    base : TypeAlias = None

    def __init__(self, db_interface):
        self.db_interface = db_interface
        _transaction.init_transactions(self)
    
    @transaction
    def create(self,data=None,**kwargs)->base:
        if not data:
            data = {}
        data = data|kwargs
        
        inst = self.base()

        for k,v in data.values():
            assert hasattr(inst,k)
            setattr(inst,k,v)
            #TODO: Raise custom exceptions!

        self.session.add(inst)

        return inst

    @transaction
    def update(self,obj:base,data=None,**kwargs)->base:
        if not data:
            data = {}
        data = data|kwargs

        for k,v in data.values(): 
            assert hasattr(obj,k)
            setattr(obj,k,v)
            #TODO: Raise custom exceptions!

        # self.session.flush()
        return obj
    
    @transaction
    def delete(self,obj)->None:
        self.session.delete(obj)
    
    @property
    def session(self):
        return c_session.get()
    @property
    def engine(self):
        return c_engine.get()
    



class db_interface():
    ''' Interface for managing the file database directly. Each instance is a locked session with a specific db. DBs should not have overlapping cached files '''
    def __init__(self,settings_file:dict|None=None,**kwargs):

        self.settings = settings_interface()
        if settings_file:
            self.settings.load_file(settings_file)
        elif kwargs:
            self.settings.set_attributes(kwargs)
        else:
            #Initilizes anyway, object throws warnings & exceptions w/a
            self.settings.set_attributes({})
        
        self.db_lock_check()
        self.db_lock_register()

        self.repo_baseclass = repo_baseclass(self)
    
    engine  = None
    session = None

    def ensure_c_engine(self):
        ''' ensure root engine exists and is assigned to contextVar c_engine '''
        if not self.engine:
            self.engine = create_engine(self.settings.database_fp)        
        c_engine.set(self.engine)
        return c_engine.get()

    def ensure_c_session(self):
        ''' create root session if it doesnt and set to self.session. If it does exist create nested session. return current session obj '''
        #Much of this is similar to transaction in examples of: https://ryan-zheng.medium.com/simplifying-database-interactions-in-python-with-the-repository-pattern-and-sqlalchemy-22baecae8d84

        if not self.engine:
            self.engine = self.ensure_c_engine()

        if not c_session.get():
            if self.session:
                c_session.set(self.session)
            else:
                c_session.set(self.engine.Session(bind=self.engine, keep_post_commit = True))

        session        = c_session.get()
        in_transaction = session.in_transaction()
        try: 
            #Yield session object(even if nested), then commit and close
            if in_transaction:
                _session = c_session.get().begin_nested()
                yield _session
                _session.commit()
                c_session.set(None)
            else:
                yield session
                session.commit()
                session.close()     
                #if not nested, close session

        except:
            #Undo and do not commit changes
            if in_transaction:
                _session.rollback() 
                c_session.set(None)
            else:
                session.rollback()  
                session.close()
            raise
     
    def db_lock_check(self):
        #Check if lock file, throw error if so
        self.settings.lock_location

    def db_lock_register(self):
        #Create the lock file
        atexit.register(self.db_lock_unregister)
        # self.settings.lock_location
        
    def db_lock_unregister(self):
        #Remove the lock file
        ...
        # self.settings.lock_location
    


