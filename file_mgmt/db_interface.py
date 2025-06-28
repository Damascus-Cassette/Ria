from .db_struct import (asc_Space_NamedFile, asc_Space_NamedSpace, File, Space, target, Export, Session, User)
import atexit

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
    
    # def __init_subclass__(cls):
    #     #could use this to update the input and return annotations of create,update,delete and other base methods
    #     base : TypeAlias = cls.base

    @transaction
    def create(self,data=None,**kwargs)->base:
        if not data:
            data = {}
        data = data|kwargs
        
        inst = self.base()

        for k,v in data.values(): setattr(inst,k,v)

        self.session.add(inst)

        return inst

    @transaction
    def update(self,obj:base,data=None,**kwargs)->base:
        if not data:
            data = {}
        data = data|kwargs

        for k,v in data.values(): setattr(obj,k,v)

        # self.session.flush()
        return obj
    
    @transaction
    def delete(self,obj)->None:
        self.session.delete(obj)
    

    @property
    def session(self):
        c_session.get()
    @property
    def engine(self):
        c_engine.get()



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
        ''' Get root engine '''
        if not self.engine:
            ... #Create engine w/ settings (ie loc and the like)
        
        c_engine = self.engine

    def ensure_c_session(self):
        ''' create root session if it doesnt and set to self.session. If it does exist create nested session. return current session obj '''
        if not self.engine:
            self.engine = self.ensure_c_engine()
        
        if not c_session:
            c_session = self.engine.Session(bind = ???, keep_post_commit = True)
            ... #Create session with args, Return.
        elif c_session.in_transaction():
            return c_session.nested_transaction()
        else:
            return c_session

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
    


