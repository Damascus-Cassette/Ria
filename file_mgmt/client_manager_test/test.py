from fastapi import FastAPI, APIRouter, Request
import functools
import inspect
from types import FunctionType
from typing import Self
import string

import requests

class connection():
    ''' 
    Manages get/post/++ connections with a specific entity.
    Should return fastapi http exceptions or sucesses

    '''
    host     : str
    port     : str
    subroute : str  #For routing to a specific subpath under the host
    user     : str|None
    password : str|None

    def __init__(self,host,port,subroute='',user=None,password=None):
        self.host     = host
        self.port     = port
        self.subroute = subroute
        self.user     = user
        self.password = password
    
    def _format_kwargs(self,**kwargs):
        if not kwargs:
            return ''
        ret = ''
        for k,v in kwargs.items():
            ret.append('?{k}={v}')
        return '?'+ret
    
    def _construct_path(self,subpath,f_kwargs):
        f_kwargs = self._format_kwargs(f_kwargs)
        return self.host+':'+self.port+subpath+'?'+f_kwargs

    def get(self,subpath,f_kwargs,**kwargs):
        assert not kwargs #Custom implimentations may want kwargs
        path = self._construct_path(subpath,f_kwargs)
        
        if self.user: return requests.get(path,auth=(self.user,self.password))
        else:         return requests.get(path)

    def post(self,subpath,f_kwargs,data,**kwargs):
        assert not kwargs #Custom implimentations may want kwargs
        path = self._construct_path(subpath,f_kwargs)
        
        if self.user: return requests.post(path,data=data,auth=(self.user,self.password))
        else:         return requests.post(path,data=data)

class api():
    @classmethod
    def construct(cls,inst,router):
        for k in dir(inst):
            v = getattr(inst,k)
            if isinstance(v,cls._base):
                v.add_api_route(inst,router)

    @classmethod
    def _wrapper(cls,base, method, path, *args,**kwargs):
        def wrapper(func):
            if issubclass(func.__class__,cls._base):
                chain = func
                func  = func.func
            else: 
                chain = None
            return base(func,path,method=method,_chain=chain,*args,**kwargs)
        return wrapper

    class _base():
        def __init__(self,func,path,method,_chain:Self=None,*args,**kwargs):
            self.func = func
            self.path = path
            self.method = method
            self.args = args
            self.kwargs = kwargs
            self.chain  = _chain
        
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
            if self.chain:
                self.chain.add_api_route(inst,router)

        def filter_fastAPI_params(self,params:dict):
            #Filter out Request and the like. TODO: Make more generic
            ret = {}
            v: inspect.Parameter
            for k,v in params.items():
                if v.annotation is not Request:
                    ret[k] = v
            return ret

        def format_args_kwargs(self,*args,**kwargs)->tuple[str,dict,dict]:
            '''Take arguments for the func and format them into path, web pathvars, and leftover kwargs '''

            func_params = dict(inspect.signature(self.func).parameters)
            func_params = self.filter_fastAPI_params(func_params)
            
            k_from_args = {}
            for x in args:
                param = func_params.pop[0]
                assert param.kind != inspect._ParameterKind.KEYWORD_ONLY
                assert param.name not in kwargs.keys()
                k_from_args[param.name] = x

            kwargs = kwargs|k_from_args

            path_keys = string.Formatter.parse('',self.path)

            #pop out and use path keys            
            f_dict = {}
            for key in path_keys: 
                f_dict[key] = kwargs.pop[key]
            path = self.path.format(f_dict)

            #Pop out what are to be path vars            
            f_kwargs = {}
            for k,v in kwargs.items: 
                if k in func_params.keys():
                    f_dict[k] = kwargs.pop[k]

            #Rest are assumed to be args for the connection objec            
            r_kwargs = kwargs
            return path, f_kwargs, r_kwargs


        def __call__(self,*args,**kwargs):
            raise Exception('_BASE HAS BEEN CALLED')


    @classmethod
    def get(cls, path, *args,**kwargs):
        return cls._wrapper(cls._get,'GET',path, *args, **kwargs)

    @classmethod
    def post(cls, path, *args,**kwargs):
        return cls._wrapper(cls._post,'POST',path, *args, **kwargs)

    class _get(_base):
        def __call__(self,connection,*args,**kwargs):
            subpath, f_kwargs, r_kwargs = self.format_args_kwargs(*args,**kwargs)
            return connection.get(subpath,f_kwargs, **r_kwargs)

    class _post(_base):
        def __call__(self, connection, data, /, *args,**kwargs):
            subpath, f_kwargs, r_kwargs = self.format_args_kwargs(*args,**kwargs)
            return connection.post(subpath,f_kwargs,data=data, **r_kwargs)


class Hello:#
    def __init__(self, name: str, con):
        self.name = name
        self.router = APIRouter()
        self.connection = con
        api.construct(self,self.router)

    def construct_path(self,function):
        return '/'+function.__name__

    @api.get('/')
    @api.get(construct_path)
    def hello(self):
        return {"Hello": self.name}
    
    @api.get('/who_am_i')
    def who_am_i(self):
        return self.name

    @api.get('/echo_test')
    def echo_connection(self):
        cls = self.__class__

        return {
            'FROM_INST' : self.name,
            'CALLED'    : cls.who_am_i(self.connection)
            }
        
import sys
app = FastAPI()

if sys.argv[-1] == 'a':
    name     = 'Instance_A'
    settings = {'host':"127.0.0.1", 'port':8003}
    con      = connection('127.0.0.1', '8002')
else:
    name     = 'Instance_B'
    settings = {'host':"127.0.0.1", 'port':8002}
    con      = connection('127.0.0.1', '8003')

import uvicorn
hello = Hello(name,con)
app.include_router(hello.router)
uvicorn.run(app, **settings)


