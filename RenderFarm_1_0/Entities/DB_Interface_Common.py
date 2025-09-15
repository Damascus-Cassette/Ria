
from sqlalchemy.orm import Session

from contextlib import contextmanager
from contextvars import ContextVar
from functools import partial, wraps

@contextmanager
def session_cm(c_engine,c_session:ContextVar, c_savepoint:ContextVar, commit = True):
    #Note: With a continuous connection this becomes in mem only!
    #Need to make a factory and distributed across interfaces

    ongoing_session = c_session.get()

    try:
        if ongoing_session:
            print('Creating New Savepoint!')
            _savepoint = ongoing_session.begin_nested()
            token2 = c_savepoint.set(_savepoint)
            yield ongoing_session

            if commit: 
                _savepoint.commit()
            else:      
                _savepoint.rollback()

        else:
            print('Creating New Session!')
            session = Session(bind=c_engine.get(), expire_on_commit = False)
            token_1 = c_session.set(session)
            
            yield session
            
            if commit: 
                session.commit()
                session.close()
            else: 
                session.rollback()
                
    except:
        if ongoing_session:
            _savepoint.rollback() 
        else:
            session.rollback()  
            session.close()
        raise

    finally:
        if ongoing_session:
            c_savepoint.reset(token2)
        else:
            c_session.reset(token_1)
            c_session.set(None)

class _transaction():
    ''' Placeholder for future complex use. I dont remember exactly why I wanted this before'''
    def __init__(self,func, c_engine, c_session_var,c_savepoint_var, filter=None):
        self.func   = func
        self.filter = filter
        self.c_session_var = c_session_var
        self.c_savepoint_var = c_savepoint_var
        self.c_engine = c_engine

    def __get__(self,inst,inst_cls):
        if inst is None:
            return self
        # return partial(self, inst)
        return wraps(self.func)(partial(self, inst))
    
    def __call__(self, inst, *args, **kwargs):
        with session_cm(self.c_engine, self.c_session_var, self.c_savepoint_var) as session:
            return self.func(inst, session, *args, **kwargs)

    @classmethod
    def _wrapper(cls, c_engine:ContextVar, c_session_var:ContextVar, c_savepoint_var:ContextVar, filter=None):
        def wrapper(func):
            return cls(func, c_engine, c_session_var, c_savepoint_var, filter=filter)
        return wrapper