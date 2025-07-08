from fastapi import FastAPI, APIRouter
import functools
import inspect
from types import FunctionType

class wrapper():
    @classmethod
    def construct(cls,inst,router):
        for k in dir(inst):
            v = getattr(inst,k)
            if isinstance(v,cls._base):
                v.add_api_route(inst,router)

    @classmethod
    def get(cls,path, *args,**kwargs):
        def wrapper(func):
            return cls._base(func,path,method='GET',*args,**kwargs)
        return wrapper

    class _base():
        def __init__(self,func,path,method,*args,**kwargs):
            self.func = func
            self.path = path
            self.method = method
            self.args = args
            self.kwargs = kwargs
        
        def create_wrapped(self,inst)->FunctionType:
            #TODO: Allow for nested wrappers via a recursive search & execution of create_wrapped?
            
            sig = inspect.signature(self.func)            

            def wrapped(*args,**kwargs):
                return self.func(inst,*args,**kwargs)

            wrapped.__signature__ = sig.replace(parameters=list(sig.parameters.values())[1:])

            return wrapped

        def api_route_args(self,inst)->tuple[tuple,dict]:
            
            wrapped = self.create_wrapped(inst)

            if callable(self.path):
                path = self.path(self,self.func)
            else:
                path = self.path
            
            return (path, wrapped),{'methods':[self.method]}

        def add_api_route(self, inst:object, router:APIRouter):
            args, kwargs = self.api_route_args(inst)
            router.add_api_route(*args, **kwargs)

        def __call__(self):
            ''' Call method via connection object or lamda '''
            raise Exception('NOT PART OF TEST YET')

class Hello:
    def __init__(self, name: str):
        self.name = name
        self.router = APIRouter()
        wrapper.construct(self,self.router)

    def construct_path(self,function):
        return '/'+function.__name__

    # @wrapper.get('/')
    @wrapper.get(construct_path)
    def hello(self):
        return {"Hello": self.name}
    
    @wrapper.get(construct_path)
    def other_func(self):
        return "NOTHING FOR YOU HERE"


app = FastAPI()
hello = Hello("SomethingNew")
app.include_router(hello.router)

import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8002)