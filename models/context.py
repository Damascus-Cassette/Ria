from contextlib  import contextmanager
from contextvars import ContextVar

graph_current    = ContextVar(default=None)
session          = ContextVar(default=None)
graph_collection = ContextVar(default=None)
