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

    def __init__(self,host,port,subroute='',mode='http://' ,user=None,password=None):
        self.host     = host
        self.port     = port
        self.subroute = subroute
        self.user     = user
        self.password = password
        self.mode = mode
     
    def _construct_path(self,subpath):
        return self.mode + self.host+':'+self.port+subpath

    def get(self,subpath,f_kwargs,**kwargs):
        assert not kwargs #Custom implimentations may want kwargs
        path = self._construct_path(subpath)
        
        if self.user: return requests.get(path,params=f_kwargs,auth=(self.user,self.password))
        else:         return requests.get(path,params=f_kwargs)

    def post(self,subpath,f_kwargs,data,**kwargs):
        assert not kwargs #Custom implimentations may want kwargs
        path = self._construct_path(subpath,f_kwargs)
        
        if self.user: return requests.post(path,params=f_kwargs,data=data,auth=(self.user,self.password))
        else:         return requests.post(path,params=f_kwargs,data=data)

class api():

    @classmethod
    def construct(cls,inst,router):
        for k in dir(inst):
            v = getattr(inst,k)
            if isinstance(v,cls._base):
                v.add_api_route(inst,router)
                setattr(inst, k, v.create_wrapped(inst))

    @classmethod
    def _wrapper(cls, base, method, path, *args, **kwargs):
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
                param = func_params.pop(0)
                assert param.kind != inspect._ParameterKind.KEYWORD_ONLY
                assert param.name not in kwargs.keys()
                k_from_args[param.name] = x

            kwargs = kwargs|k_from_args

            path_keys = [x[1] for x in string.Formatter.parse('',self.path) if x[1]]

            #pop out and use path keys            
            f_dict = {}
            for key in path_keys:
                
                f_dict[key] = kwargs.pop(key)
            path = self.path.format(f_dict)

            #Pop out what are to be path vars            
            f_kwargs = {}
            for k,v in kwargs.items(): 
                if k in func_params.keys():
                    f_dict[k] = kwargs.pop(k)

            #Rest are assumed to be args for the connection objec            
            r_kwargs = kwargs
            return path, f_kwargs, r_kwargs

        def format_data_from_response(self,response):
            '''Format w/a, check if json compatable first'''
            #TODO: FUCGLY AS FUCK

            sig = inspect.signature(self.func)
            ret_anno = sig.return_annotation
            
            try:
                value = response.json()
                try:
                    if ret_anno is not inspect._empty:
                        value = ret_anno(value)
                    else:
                        value = value
                except:
                    value = response.json()
            except:
                value = response.content 
            finally:
                return value 

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
            response, f_data = self.call(connection, *args,**kwargs)
            return f_data

        def call(self, connection, /, *args,**kwargs)->requests.Response:
            subpath, f_kwargs, r_kwargs = self.format_args_kwargs(*args,**kwargs)
            response = connection.get(subpath,f_kwargs, **r_kwargs)
            return response, self.format_data_from_response(response)

    class _post(_base):
        def __call__(self, connection, data, /, *args,**kwargs):
            response, f_data = self.call(connection, data, *args,**kwargs)
            return f_data

        def call(self, connection, data, /, *args,**kwargs)->requests.Response:
            subpath, f_kwargs, r_kwargs = self.format_args_kwargs(*args,**kwargs)
            response = connection.post(subpath,f_kwargs,data=data, **r_kwargs)
            return response, self.format_data_from_response(response)


class net_io():
    def __init_subclass__(cls):
        api_attrs={}
        for k in dir(cls):
            v = getattr(cls,k)
            if isinstance(v,api._base):
                api_attrs[k] = v
        setattr(cls,'api',type('api_object',(object,),api_attrs))

class Hello(net_io):
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
        return {
            'FROM_INST' : self.name,
            'CALLED'    : self.api.who_am_i(self.connection)
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


