from typing      import Any,TypeAlias,get_type_hints
from contextlib  import contextmanager
from contextvars import ContextVar
from functools   import wraps

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
    def create(cls,obj = None,data=None, **kwargs)->base:
        assert isinstance(obj,cls.base)
        session = cls.c_session.get()
        if not data:
            data = {}
        data = data|kwargs
        
        if not obj:
            obj = cls.base()        

        for k,v in data.items():
            assert hasattr(obj,k)
            setattr(obj,k,v)

        if getattr(cls.base,'_use_merge',False):
            session.merge(obj)
        else:
            session.add(obj)

        return obj

    @transaction
    def update(cls,obj:base,data=None,**kwargs)->base:
        assert isinstance(obj,cls.base)
        # session = cls.c_session.get()

        if not data:
            data = {}
        data = data|kwargs

        for k,v in data.items(): 
            assert hasattr(obj,k)
            setattr(obj,k,v)
        return obj
    
    @transaction
    def delete(cls,obj, *args,**kwargs)->None:
        assert isinstance(obj,cls.base)

        if func := getattr(obj,'on_delete',None):
            func(*args,**kwargs)

        session = cls.c_session.get()
        session.delete(obj)

    @classmethod
    def echo_context(cls,c_attr)->str:
        return getattr(cls.context,c_attr,None).get()

