from functools import partial
from contextvars import ContextVar
from .DB_Interface_Common import _transaction, session_cm

ClientDb_c_Engine    = ContextVar('ClientDb_c_Engine' , default = None) 
ClientDb_c_session   = ContextVar('JobDb_c_session'   , default = None) 
ClientDb_c_savepoint = ContextVar('JobDb_c_savepoint' , default = None)
ClientDB_Transaction = partial(_transaction._wrapper, ClientDb_c_Engine, ClientDb_c_session, ClientDb_c_savepoint)
ClientDB_Session_CM  = partial(session_cm, ClientDb_c_Engine ,ClientDb_c_session ,ClientDb_c_savepoint)