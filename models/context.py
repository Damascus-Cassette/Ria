from contextlib  import contextmanager
from contextvars import ContextVar

session          = ContextVar(default=None)
graph_collection = ContextVar(default=None)
graph_current    = ContextVar(default=None)
