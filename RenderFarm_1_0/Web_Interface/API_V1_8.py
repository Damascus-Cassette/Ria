
from fastapi     import APIRouter, Response, Request, Depends, FastAPI, WebSocket, WebSocketDisconnect
from enum        import Enum
from functools   import partial
from inspect     import signature, isclass, iscoroutinefunction, _empty
from string      import Formatter
from types       import FunctionType
from contextlib  import contextmanager
from contextvars import ContextVar
import requests
from functools import wraps


_CONNECTION_TARGET = ContextVar('_CONNECTION_TARGET',default = None)
_LOCAL_ENTITY = ContextVar('_LOCAL_ENTITY',default = None)

class Commands(Enum):
    GET       = 'GET'
    POST      = 'POST'
    PATCH     = 'PATCH' 
    PUT       = 'PUT'
    DELETE    = 'DELETE'
    WEBSOCKET = 'WEBSOCKET'

class IO():

    send_func   = None
    send_args   = None
    send_kwargs = None

    fapi_router : APIRouter

    def __init__(self, command, func, router, path, *args, **kwargs):
        self.command       =  command
        self.func          =  func
        self.fapi_router   =  router
        self.path          =  path
        self.args          =  args
        self.kwargs        =  kwargs


    
    def _register(self, container, this_entity):
        ''' Access through dict to avoid __get__ I think? '''
        if self.command is Commands.WEBSOCKET:
            self._register_websocket(container,this_entity)
        self._register_regular(container, this_entity)
        return self.fapi_router

    def _register_websocket(self, container, this_entity):
        _args,_kwargs = self._api_router_args_websocket_(container,this_entity)
        self.fapi_router.add_api_websocket_route(*_args,**_kwargs)

    def _api_router_args_websocket_(self, container, this_entity):
        wrapped = self._api_route_wrapped_func_websocket_(container, this_entity)
        path    = self.path
        return (path, wrapped, self.func.__name__) + self.args, self.kwargs

    def _register_regular(self, container, this_entity):
        _args,_kwargs = self._api_router_args_regular_(container,this_entity)
        self.fapi_router.add_api_route(*_args,**_kwargs)
    
    def _api_router_args_regular_(self, container, this_entity):
        wrapped = self._api_route_wrapped_func_regular_(container, this_entity)
        path    = self.path
        return (path, wrapped) + self.args, {'methods':[self.command.value]} | self.kwargs

    def _api_route_wrapped_func_websocket_(self, container, this_entity):
        func = self.func
        sig = signature(func)
        
        if iscoroutinefunction(func):
            async def wrapped(websocket:WebSocket, *args, _foreign_entity = Depends(this_entity.Find_Entity_From_WsReq), **kwargs):
                t =  _LOCAL_ENTITY.set(this_entity)
                res = await func(container,this_entity,_foreign_entity, websocket, *args,**kwargs)
                _LOCAL_ENTITY.reset(t)
                return res

        else:
            def wrapped(websocket:WebSocket, *args, _foreign_entity = Depends(this_entity.Find_Entity_From_WsReq), **kwargs):
                t =  _LOCAL_ENTITY.set(this_entity)
                res =  func(container,this_entity,_foreign_entity, websocket, *args,**kwargs)
                _LOCAL_ENTITY.reset(t)
                return res

        params = signature(wrapped).parameters
        wrapped.__name__      = func.__name__

        o_args   = [x for x in list(sig.parameters.values())[4:] if x.POSITIONAL_OR_KEYWORD] 
        o_kwargs = [x for x in list(sig.parameters.values())[4:] if (not x.POSITIONAL_OR_KEYWORD) and x.KEYWORD_ONLY]

        parameters        = (params['websocket'], *o_args, params['_foreign_entity'], *o_kwargs)
        return_annotation = sig.return_annotation

        wrapped.__signature__ = sig.replace(
            parameters        = parameters,
            return_annotation = return_annotation,)

        return wrapped


    def _api_route_wrapped_func_regular_(self, container, this_entity):
        func = self.func
        sig = signature(func)
        
        if iscoroutinefunction(func):
            async def wrapped(request:Request, *args, _foreign_entity = Depends(this_entity.Find_Entity_From_Req), **kwargs):
                t =  _LOCAL_ENTITY.set(this_entity)
                res = await func(container,this_entity,_foreign_entity, request, *args,**kwargs)
                _LOCAL_ENTITY.reset(t)
                return res

        else:
            def wrapped(request:Request, *args, _foreign_entity = Depends(this_entity.Find_Entity_From_Req), **kwargs):
                t =  _LOCAL_ENTITY.set(this_entity)
                res =  func(container,this_entity,_foreign_entity, request, *args,**kwargs)
                _LOCAL_ENTITY.reset(t)
                return res

        params = signature(wrapped).parameters
        wrapped.__name__      = func.__name__

        o_args   = [x for x in list(sig.parameters.values())[4:] if x.POSITIONAL_OR_KEYWORD] 
        o_kwargs = [x for x in list(sig.parameters.values())[4:] if (not x.POSITIONAL_OR_KEYWORD) and x.KEYWORD_ONLY]

        parameters        = (params['request'], *o_args, params['_foreign_entity'], *o_kwargs)
        return_annotation = sig.return_annotation

        wrapped.__signature__ = sig.replace(
            parameters        = parameters,
            return_annotation = return_annotation,)

        return wrapped

    # def _register_websocket
    # def _api_router_args_websocket_
    # def _api_route_wrapped_func_websocket_

    @classmethod
    def _wrapper(cls,cmd,router,path,*args,**kwargs):
        def wrapper(func): 
            return cls(cmd,func,router,path,*args,**kwargs)
        return wrapper
    
    @classmethod
    def Get(cls,router,path,*args,**kwargs): return cls._wrapper(Commands.GET,router,path,*args,**kwargs)
    @classmethod
    def Post(cls,router,path,*args,**kwargs): return cls._wrapper(Commands.POST,router,path,*args,**kwargs)
    @classmethod
    def Delete(cls,router,path,*args,**kwargs): return cls._wrapper(Commands.DELETE,router,path,*args,**kwargs)
    @classmethod
    def Patch(cls,router,path,*args,**kwargs): return cls._wrapper(Commands.PATCH,router,path,*args,**kwargs)
    @classmethod
    def Put(cls,router,path,*args,**kwargs): return cls._wrapper(Commands.PUT,router,path,*args,**kwargs)
    @classmethod
    def Websocket(cls,router,path,*args,**kwargs): return cls._wrapper(Commands.WEBSOCKET,router,path,*args,**kwargs)
    


    def Send(self,*args,**kwargs):
        ''' Only accessable during construction, due to __get__ '''
        def wrapper(func):
            self.send_func   = func
            self.send_args   = args
            self.send_kwargs = kwargs
            return func
        return wrapper

    def Client(self,*args,**kwargs):
        ''' Wrap a websocket connection function to be declarativly typed '''
        def wrapper(func):
            assert self.command is Commands.WEBSOCKET
            self.send_func   = self._Wrap_WS_Client(func)
            self.send_args   = args
            self.send_kwargs = kwargs
            return func
        return wrapper
    
    def _Wrap_WS_Client(self,func):
        @wraps(func)
        async def wrapper(container, this_entity, other_entity, raw_path,*args,**kwargs):   
            args, kwargs, path = self._format_path_consume(self._send_fmt_func, raw_path, args, kwargs, ignore_slice_start=5)
            print('ARGS IS'   , args)
            print('KWARGS IS' , kwargs)
            headers = this_entity.export_header(other_entity) | other_entity.export_header(this_entity)
            res = await func(container,this_entity,other_entity,path,headers,*args,**kwargs)
            print('RES IS:', res)
            return res
        return wrapper 
    
    def __get__(self,inst,inst_cls):
        if inst is None:
            return self
        return partial(self,inst)

    def __call__(self, container, *args, local_entity=None, **kwargs):
        ''' Direct call is to send function '''
        if not local_entity:
            assert _LOCAL_ENTITY.get()
            local_entity =_LOCAL_ENTITY.get()
        
        # print('__call__ ARGS  : ', args)
        # print('__call__ KWARGS: ', kwargs)

        assert _CONNECTION_TARGET.get()
        this_entity =_CONNECTION_TARGET.get()
        assert issubclass(this_entity.__class__ ,Foreign_Entity_Base)
        assert issubclass(local_entity.__class__,Local_Entity_Base)

        raw_path = container.get_path() + self.fapi_router.prefix + self.path
        return self._send(container,this_entity,local_entity,raw_path,*args,**kwargs)

    @property
    def _send(self):
        ''' Header for send functions of each type'''
        if self.send_func:
            return self.send_func

        match self.command:
            case Commands.GET:       return self._send_get_default
            case Commands.POST:      return self._send_post_default
            case Commands.DELETE:    return self._send_delete_default
            case Commands.PUT:       return self._send_put_default
            case Commands.PATCH:     return self._send_patch_default
            case Commands.WEBSOCKET:
                raise Exception(f'Websocket Client function must be declared!')
            case _:
                raise Exception(f'Command Not Found For Send! {self.command}')
            
    @property
    def _send_fmt_func(self):
        if self.send_func: return self.send_func 
        return self.func
        

    # def _send_get(self,container,this_entity,other_entity,raw_path,*args,**kwargs):
    #     # if self.send_func:
    #     #     return self.send_func(container,this_entity,other_entity,raw_path,*args,**kwargs)
    #     # else:
    #     return self._send_get_default(container,this_entity,other_entity,raw_path,*args,**kwargs)

    def _send_get_default(self,container, this_entity, other_entity,raw_path,*args,**kwargs):   
        args, kwargs, path = self._format_path_consume(self._send_fmt_func, raw_path, args, kwargs)
        return this_entity.get(other_entity,path,*args,**kwargs)

    def _send_post_default(self,container, this_entity, other_entity,raw_path,*args,**kwargs):   
        args, kwargs, path = self._format_path_consume(self._send_fmt_func, raw_path, args, kwargs)
        return this_entity.post(other_entity,path,*args,**kwargs)

    def _send_delete_default(self,container, this_entity, other_entity,raw_path,*args,**kwargs):   
        args, kwargs, path = self._format_path_consume(self._send_fmt_func, raw_path, args, kwargs)
        return this_entity.delete(other_entity,path,*args,**kwargs)

    def _send_put_default(self,container, this_entity, other_entity,raw_path,*args,**kwargs):   
        args, kwargs, path = self._format_path_consume(self._send_fmt_func, raw_path, args, kwargs)
        return this_entity.put(other_entity,path,*args,**kwargs)

    def _send_patch_default(self,container, this_entity, other_entity,raw_path,*args,**kwargs):   
        args, kwargs, path = self._format_path_consume(self._send_fmt_func, raw_path, args, kwargs)
        return this_entity.patch(other_entity,path,*args,**kwargs)

    def _format_path_consume(self, func, raw_path, args, kwargs, ignore_slice_start = 4):
        '''convert all to kwargs by key and order, pop and format string, convert back and return.
        if there is a missing input, throw exception for unformatted path '''
        sig = signature(func)
        
        _args   = []
        _kwargs = {}
        _fmt    = {}

        keys = [x[1] for x in Formatter().parse(raw_path) if x[1] is not None]
        
        for i,(k,v) in enumerate(list(sig.parameters.items())[ignore_slice_start:]):
            # print(i,k,v)
            # this_e, other_e and raw_path
            if k in keys:
                _fmt[k] = v
                continue
            if v.POSITIONAL_ONLY:
                _args.append(args[i])
            elif v.POSITIONAL_OR_KEYWORD or v.KEYWORD_ONLY:
                if k in kwargs.keys():
                    _kwargs[k] = kwargs[k]
                elif v.default is not _empty:
                    _kwargs[k] = v.default
                else:
                    _kwargs[k] = None
                    
        # print('FORMAT_CONSUME RETURN input args   : ', args)
        # print('FORMAT_CONSUME RETURN input kwargs : ', kwargs)
        # print('FORMAT_CONSUME RETURN _args   : ',_args)
        # print('FORMAT_CONSUME RETURN _kwargs : ',_kwargs)
        path = raw_path.format(_fmt)
        return _args, _kwargs, path 
    

class Interface_Base():
    Route_Subpath = ''

    def __init__(self, parent=None):        
        ''' Initialize all child instances of the router interface '''
        self.parent = parent
        self._on_new(self)

    def get_path(self):
        if self.parent:
            return  self.parent.get_path() + self.Route_Subpath
        return ''

    @staticmethod
    def _on_new(inst):
        ''' Intialize Interface Structure '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if not isclass(v):
                continue
            if issubclass(v,Interface_Base):
                setattr(inst,k,v(inst))

    @staticmethod
    def _iter_insts(inst):
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if isclass(v): continue
            if issubclass(v.__class__,Interface_Base) or (v.__class__ is Interface_Base):
                yield v

    def _register(self,local_entity,p_router:APIRouter):
        # applicable = [v for k,v in self.__dict__.items() if (not k.startswith('_')) and (isinstance(v,IO))]
        # print('REGISTERING SELF', self)
        # for k,v in self.__dict__.items():

        for k in dir(self):
            if k.startswith('_'): continue
            v = getattr(self.__class__,k,None)
            if isinstance(v,IO):
                v._register(self,local_entity)


        for k in dir(self):
            if isinstance(v:=getattr(self,k), APIRouter):
                p_router.include_router(v, prefix = getattr(self,'Route_Subpath',''),)

class Foreign_Entity_Base:    
    ''' Foreign Entity Base class, Gives the post commands and ensures formatting on subclasses '''
    def __init_subclass__(cls):
        assert hasattr(cls, '__tablename__' )
        assert hasattr(cls, 'Entity_Type' )
        if cls._interactive:
            assert hasattr(cls, 'export_header'   )
            assert hasattr(cls, 'intake_request'  )
            assert hasattr(cls, 'matches_request' )
            assert hasattr(cls, 'export_auth'     )
            # assert hasattr(cls, 'New_From_Request')
    _interactive  = True      #If Undec/Unknown w/out interface this is false to not check structure
    
    export_header  : FunctionType
    intake_header  : FunctionType
    matches_header : FunctionType
    export_auth    : FunctionType

    host : str
    port : str
    mode : str = 'http://'

    def _cast_responce(self, res : requests.Response)->Request:
        if isinstance(res,Response): return res
        return Response(
            content     = res.content,
            status_code = res.status_code,
            headers     = res.headers,
            # media_type  = res.media_type,
        )

    def _domain(self)->str:
        assert not (self.mode is None)
        assert not (self.host is None)
        assert not (self.port is None)

        return self.mode + self.host+':'+self.port

    def get(self, from_entity, path:str, _raw_responce=False, **kwargs):
        header = self.export_header(from_entity) | from_entity.export_header(self)
        auth   = self.export_auth(from_entity)
        res = requests.get(self._domain()+path, params=kwargs, auth = auth, headers=header)
        # print('OUTGOING GET RES:', res.content)
        if _raw_responce: return res
        else:             return res.content

    def patch(self, from_entity, path:str, _raw_responce=False, **kwargs): 
        header = self.export_header(from_entity) | from_entity.export_header(self)
        auth   = self.export_auth(from_entity) 
        res = requests.patch(self._domain()+path, params=kwargs, auth = auth, headers=header)
        if _raw_responce: return res
        else:             return res.content

    def post(self, from_entity, path:str, _raw_responce=False, **kwargs): 
        header = self.export_header(from_entity) | from_entity.export_header(self)
        auth   = self.export_auth(from_entity) 
        res = requests.post(self._domain()+path, params=kwargs, auth = auth, headers=header)
        if _raw_responce: return res
        else:             return res.content

    def delete(self, from_entity, path:str, _raw_responce=False, **kwargs): 
        header = self.export_header(from_entity) | from_entity.export_header(self)
        auth   = self.export_auth(from_entity) 
        res = requests.delete(self._domain()+path, params=kwargs, auth = auth, headers=header)
        if _raw_responce: return res
        else:             return res.content

    def put(self, from_entity, path:str, data, _raw_responce=False, **kwargs): 
        header = self.export_header(from_entity) | from_entity.export_header(self)
        auth   = self.export_auth(from_entity) 
        res = requests.put(self._domain()+path, params=kwargs,data=data, auth = auth, headers=header)
        if _raw_responce: return res
        else:             return res.content

    @contextmanager
    def Active(self):
        t = _CONNECTION_TARGET.set(self)
        yield
        _CONNECTION_TARGET.reset(t)

class Local_Entity_Base():
    ''' Local Entity base class, registration as app and container for interacting with external connections '''
    export_header : FunctionType
    attach_to_app : FunctionType
    is_local      = True

    engine       : ...
    SessionMaker : ...
    session      : ...

    def __init_subclass__(cls):
        assert hasattr(cls, 'Entity_Type'   )
        assert hasattr(cls, 'export_header' )
    
    def __init__(self):
        Interface_Base._on_new(self)

    def attach_to_app(self, app:FastAPI):
        for v in Interface_Base._iter_insts(self):
            v._register(self, app)
        return app
    
    async def Find_Entity_From_Req(self, request:Request):
        ''' Ensure DB Connection, return foreign item '''
        raise NotImplementedError('Implament in Local_Class!')

    async def Find_Entity_From_WsReq(self, request:WebSocket):
        ''' Ensure DB Connection in websocket context, return foreign item '''
        raise NotImplementedError('Implament in Local_Class!')
    


# class Client_Websocket_Wrapper_Base():
#     websocket    : WebSocket

#     def __init__(self, local_entity, foreign_entity, websocket:WebSocket_Client):        
#         ...

#     def __getattr__(self, key):
#         if key not in dir(self):
#             return getattr(self.websocket, key)
#         return vars(self)[key]

#     @wraps(WebSocket_Client.Connect)
#     async def connect(self):
#         res = await self.websocket.connect()
#         self.local_entity.websocket_as_client_pool.append(self)
#         return res 
        
#     @wraps(WebSocket_Client.accept)
#     async def accept(self):
#         self.local_entity.websocket_as_client_pool.append(self)
#         return await self.websocket.accept()

#     @wraps(WebSocket_Client.close)
#     async def close(self):
#         await self.websocket.close()
#         self.local_entity.websocket_as_manager_pool.remove(self)