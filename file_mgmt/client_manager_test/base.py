from fastapi  import FastAPI, HTTPException, Request, Response, APIRouter
from pydantic import BaseModel
import string
import requests
import functools
class message(BaseModel):
    name     : str
    contents : str

objects = {}

class conn(BaseModel):
    def __init__(self,host, port):
        self.host = host
        self.port = port
    host : str 
    port : str 

    def post(self, subpath:str='/', data=None, kwargs={}):
        #This way I can later abstract out this class to allow two way communication easier?
        full_path = self.host+':'+self.port + subpath + self.format_kwargs(**kwargs)
        return requests.post(full_path, data=data)

    def format_kwargs(self,**kwargs):
        if not kwargs:
            return ''
        ret = ''
        for k,v in kwargs.items():
            ret.append('?{k}={v}')
        return '?'+ret

# @app.post('/Message')
# def post_to(data:message):
#     objects[data.name] = data

# @app.get('/Message/{msgname}')
# def show_message(msgname:str)->message:
#     if msgname not in objects.keys():
#         raise HTTPException(status_code=404, detail=f'{msgname} is not recorded!')
#     return objects[msgname]


class wrapper():
    @classmethod
    def construct(cls, cls_inst, app:FastAPI):
        for k in dir(cls_inst):
            v = getattr(cls_inst,k)
            if isinstance(v,cls._post):
                print(k)
                setattr(cls_inst,k,v.construct(cls_inst,app))
            elif isinstance(v,cls._get):
                print(k)
                setattr(cls_inst,k,v.construct(cls_inst,app))

    
    @classmethod
    def post[T](cls,path,*args,**kwargs)->T:
        def temp_wrapper(func):
            return cls._post(func,path,args,kwargs)
        return temp_wrapper    
    @classmethod
    def get[T](cls,path,*args,**kwargs)->T:
        def temp_wrapper(func):
            return cls._get(func,path,args,kwargs)
        return temp_wrapper
        

    class _post():
        ''' wrapper class that when called post via towards a connection with data, interpretting path vars and funcs type hints '''
        method ='POST'

        def __init__(self,func,path,args,kwargs):
            self.func = func
            self.path = path
            self.args = args
            self.kwargs = kwargs
            self.path_kargs = string.Formatter.parse('',path)

        def __call__(self,connection:conn,data,**kwargs):
            path_append = [kwargs.pop[x] for x in self.path_kargs]
            subpath = '/'+'/'.join(path_append)
            connection.post(subpath=subpath,data=data,kwargs=kwargs)

        def construct(self,cls_inst,app):
            print(cls_inst,app,self.func)
            cls_inst.router.add_api_route(self.path, self.func, methods=[self.method])

    class _get(_post):
        method = 'GET'

        def __call__(self,connection:conn,**kwargs):
            path_append = [kwargs.pop[x] for x in self.path_kargs]
            subpath = '/'+'/'.join(path_append)
            connection.get(subpath=subpath,kwargs=kwargs)

w=wrapper

    

class manager():
    app : FastAPI
    client : conn = 'No last client'
    
    def __init__(self):
        self.router = APIRouter()
        self.app = FastAPI()
        wrapper.construct(self,self.app)
        self.app.include_router(self.router)

    @w.get('/')
    def base_page(self)->message:
        # return 'HELLO!'
        return message(name = 'client or manager', contents = 'Base page')

    @w.get('/last')
    def last_client(self)->message:
        return message(name = 'last-client', contents = self.client)
        ...


    @w.post('/{a}')
    def manager_echo(self, request:Request, a:str, data:message)->message:
        
        print(f'RECIEVED MESSAGE VIA POST ON /{a}')
        print(data.contents)

        host = request.host.host 
        port = request.host.port 
        self.client = conn(host=host, port=port)        
        
        return message(name='Manager_Confirm', contents=f'Confirmation from manager, return to {host}:{port} from url /{a}')


class client():
    app : FastAPI
    manager : conn
    
    def __init__(self):
        self.router = APIRouter()
        self.app = FastAPI()
        wrapper.construct(self,self.app)
        self.app.include_router(self.router)

    @w.get('/')
    def base_page()->message:
        return message(name = 'client or manager', contents = 'Base page')

    @w.post('/connect')
    def manager_connect(self,conn:conn)->message:
        if conn.ping():
            message(name = 'Manager_Connect', contents = 'Manager Connected!')
            self.manager = conn
        else:
            message(name = 'Manager_Connect', contents = 'Manager failed to connect!')

    @w.post('/call')
    def call_manager(self)->message:
        self.manager
        
        msg = message(name='Manager_Call',contents='Calling to manager, expecting reuturn!')

        responce = manager.manager_echo(self.manager, a='string', data=msg)

        return responce
    
    @w.get('/last_client/')
    def route_manager_last_client(self):
        return manager.last_client(self.manager)
    

# async def main():
#     await asyncio.gather(
#         uvicorn.run(m.app, host="0.0.0.0", port=8000),
#         uvicorn.run(c.app, host="0.0.0.0", port=8001),
#     )

# # asyncio.run(main())
# if __name__ == '__main__':
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(main())

c = client()
m = manager()
import os
import uvicorn
import sys

if sys.argv[-1]=='client':
    uvicorn.run(c.app, host="127.0.0.1", port=8000)
elif sys.argv[-1]=='manager':
    uvicorn.run(m.app, host="127.0.0.1", port=8001)
else:
    raise Exception(sys.argv[-1])