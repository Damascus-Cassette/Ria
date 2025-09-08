''' New version of the interface that uses instance 'singletons' per interface. 
OL function remains the same.
'''


from types       import FunctionType
from contextlib  import contextmanager
from contextvars import ContextVar
from inspect     import isclass, iscoroutinefunction, signature as _sig
import requests
from functools   import partial, wraps
from fastapi     import FastAPI, APIRouter,Request, Depends, Response
from copy        import copy
from typing      import Self, Any
from enum        import Enum
class _UNSET  : ''' Static Unset local to file '''
# class LOCAL   : ''' Internal for type Anno '''
# class FOREIGN : ''' External for type Anno '''

class Command(Enum):
    GET       = 'GET'
    POST      = 'POST'
    PATCH     = 'PATCH'
    DELETE    = 'DELETE'
    # WEBSOCKET = 'WEBSOCKET'

# BASE = declarative_base()

# ACTIVE_ENTITY         = ContextVar('ACTIVE_ENTITY'      , default = None)
_CONNECTION_TARGET    = ContextVar('_CONNECTION_TARGET' , default = None)
_INIT_ORIGIN          = ContextVar('_INIT_ORIGIN'       , default = None) #Init origin for interface instances. Simplfies a bit.


# async def Find_Entity_From_Req(Incoming_Req):
#     assert ACTIVE_ENTITY
#     return await ACTIVE_ENTITY.get().Find_Entity_From_Req(Incoming_Req)
    


class _def_dict_list(dict):
    def _web_repr_(self)->dict:
        res = {}
        for k,v in self.items():
            res[k] = ls = []
            for e in v:
                ls.append(getattr(e,'_web_repr_',e.__repr__()))
        return res
    
    def _each_subitem_(self):
        for k,v in self.items():
            for e in v:
                yield k,e
    
    def __missing__(self,key):
        self[key] = res = []
        return res

class _method():
    ''' Local inst-method cls '''
    def __get__(self, inst, inst_cls):
        if inst is None:
            return self
        else:
            return partial(self,inst)

    def __init__(self, func):
        self.func = func
    
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class _ol_func_item():
    ''' Container for a function & it's evaluation '''
    
    def __init__(self,func,key=None,filter=True):
        self.func          = func
        self.key           = key
        self.filter        = filter
        
    def execute(self, container, this_entity, other_entity, *args,**kwargs):
        return self.func(container,this_entity, other_entity, *args,**kwargs)

    def match(self,mode:Command,this_entity,other_entity,request:Request):
        raise Exception('Child class expected to handle this')
    
    @classmethod
    def _wrapper(cls, parent:'_OL_Container', mode, key=None, *args,**kwargs):
        ''' THis is the wrapper added on the interface itself, 
        it returns the original function and adds the instance of this housing classe (_ol_func_item or inheritors) to the _OL_func_container        
        '''
        def wrapper[F](func:F)->F:

            if isinstance(func,(_ol_func_item_deliver,_ol_func_item_recieve)):
                func = func.func
            elif isinstance(func,_OL_Container):
                func = func._origin_func
            
            inst = cls(func,*args,**kwargs)
            parent.add_func_container(mode,inst)
            if key: parent.add_func_direct(key,inst)
            
            return _method(func)

        return wrapper

class _ol_func_item_recieve(_ol_func_item):
    ''' Ext -- calling -> Int '''

    def __init__(self,func, key=None, filter=True, default_deliver=False):
        self.func             = func
        self.key              = key
        self.filter           = filter
        self.default_deliver  = default_deliver

    def __call__(self, *args, **kwds):
        return self.func(*args, **kwds)
    
    def match(self,mode:Command,this_entity:'Local_Entity_Base',other_entity:'Foreign_Entity_Base',request:Request):
        assert issubclass(this_entity.__class__ , Local_Entity_Base)
        assert issubclass(other_entity.__class__, Foreign_Entity_Base)

        if isinstance(self.filter, bool):
            return self.filter
        return self.filter(mode,this_entity,other_entity,request)

class _ol_func_item_deliver(_ol_func_item):
    ''' Int -- calling -> Ext '''
    
    def __call__(self, *args, **kwds):
        return self.func(*args, **kwds)

    def match(self,mode:Command,this_entity:'Foreign_Entity_Base',other_entity:'Local_Entity_Base'):
        assert issubclass(this_entity.__class__ , Foreign_Entity_Base)
        assert issubclass(other_entity.__class__, Local_Entity_Base)

        if isinstance(self.filter, bool):
            return self.filter
        return self.filter(mode,this_entity,other_entity)


class _OL_Container():
    ''' Instance of the an overloaded function '''

    def __init__(self, func, path, *args,**kwargs):
        self._origin_func = func
        self._path        = path
        self._f_args      = args
        self._f_kwargs    = kwargs
        self._container   = None
        self._reciever_functions  :_def_dict_list[str,_ol_func_item_recieve] = _def_dict_list()
        self._delivery_functions  :_def_dict_list[str,_ol_func_item_deliver] = _def_dict_list()

    @classmethod
    def _wrapper(cls,*args,**kwargs):
        def wrapper(func):
            return cls(func,*args,**kwargs)
        return wrapper

    @classmethod
    def _on_new(cls,inst):
        ''' Utility, Call on new item to setup 'views' 
        creates local shallow copies w/ parent fixed '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if isinstance(v,cls):
                if not (v._container is inst): 
                    setattr(inst,k,v._view(inst))
    
    @staticmethod
    def _iter_insts(inst):
        ''' Intialize Interface Structure '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if isclass(v):
                continue
            if issubclass(v.__class__,_OL_Container) or (v.__class__ is _OL_Container):
                yield v

    def _view(self,container):
        new = copy(self)
        new._container = container
        return new
    
    def __call__(self, mode, other_entity, request=None, *args, **kwargs):
        ''' Unfortunatly does require other entity to be declared as far as I can tell '''
        #TODO: Convert above to have _ prefixes
        this_entity = self._container.root_entity
        recieving = issubclass(this_entity.__class__, Local_Entity_Base) 
    
        if recieving:
            assert request is not None
            func = self.find_recieving (mode,this_entity,other_entity,request)
            return func(self._container, this_entity, other_entity, *args, **kwargs)
        else: 
            raw_path = self._get_raw_path_()
            func = self.find_delivering(mode, this_entity, other_entity)
            return func(self._container, this_entity, other_entity, raw_path, *args, **kwargs)

    def _get_raw_path_(self):
        return f'{self._container._get_raw_path_()}/{self._path}'

    def find_recieving(self, mode, this_entity,other_entity,request):
        # raise Exception('FIND RECIEVING' , mode, this_entity, other_entity)
        for item in self._reciever_functions[mode]:
            item : _ol_func_item_recieve
            if item.match(mode, this_entity, other_entity, request):
                return item
        raise Exception('COULD NOT FIND MATCHING ENDPOINT WITH:', mode, this_entity ,other_entity )
        # return self._origin_func
            
    def find_delivering(self, mode, this_entity,other_entity):
        for item in self._delivery_functions[mode]:
            item : _ol_func_item_deliver
            if item.match(mode, this_entity ,other_entity):
                return item
        raise Exception('COULD NOT FIND MATCHING DELIVERY POINT WITH:', mode, this_entity ,other_entity )
        # return self._origin_func


    def add_func_container(self,mode,func_item:_ol_func_item):
        if   isinstance(func_item,_ol_func_item_deliver):
            if hasattr(func_item, 'default_deliver'):
                self._reciever_functions[mode].append( _ol_func_item_deliver(func= self._default_delivier(mode,func_item.func)  , key=func_item.key, filter=func_item.filter))
            return self._delivery_functions[mode].append(func_item)
        elif isinstance(func_item,_ol_func_item_recieve):
            return self._reciever_functions[mode].append(func_item)
        raise Exception('COULD NOT INTAKE', mode, func_item.func.__name__)

    def add_func_direct(self,key,func):
        if hasattr(self,key):
            raise Exception(f'{self} SETUP ERROR: "{key}" already in use by {getattr(self,key)}' )
        setattr(self,key,func)

    def _register(self, router, args=None, kwargs=None):
        ''' Registers reciever functions to contextual entity pool '''
        for mode, func_list in self._reciever_functions.items():
            face_ol_item : _ol_func_item_recieve = func_list[0] #First func in list is used to define the interface.
            # _args,_kwargs = face_func._api_route_args(self._container._root_entity, self._container, self, router, *args, **kwargs)
            _args,_kwargs = self._api_router_args_(face_ol_item, mode, args, kwargs)
            router.add_api_route(*_args,**_kwargs)

    def _api_router_args_(self, face_ol_item:_ol_func_item_recieve, mode:Enum, args=None, kwargs=None)->tuple[tuple,dict]:
        if kwargs is None: kwargs = {}
        if args   is None: args   = tuple()

        wrapped = self._api_route_wrapped_func_(face_ol_item, mode)
        path    = self._path

        return (path, wrapped) + self._f_args + args, {'methods':[mode.value]} | self._f_kwargs | kwargs

    def _api_route_wrapped_func_(self, face_ol_item:_ol_func_item_recieve, mode)->FunctionType:
        func = face_ol_item.func
        sig = _sig(func)
        
        if not iscoroutinefunction(func):
            async def wrapped(request:Request, _ext_entity =Depends(self._container.root_entity.Find_Entity_From_Req),*args,**kwargs):
                return self(mode, _ext_entity, request, *args,**kwargs)
        else:
            def wrapped(request:Request, _ext_entity =Depends(self._container.root_entity.Find_Entity_From_Req),*args,**kwargs):
                return self(mode, _ext_entity, request, *args,**kwargs)

        #Depends(_async_...) as a bind to primary thread, trying to ensure syncronous execution
        #UNTESTED. Rn trying to do execution.

        wrapped.__name__      = func.__name__
        wrapped.__signature__ = sig.replace(
            parameters        = [_sig(wrapped).parameters['request'], _sig(wrapped).parameters['_ext_entity'], *list(sig.parameters.values())[3:]], 
            return_annotation = sig.return_annotation )
        #Spoof signature to that of wrapped_request + original for fastapi's introspection
        
        return wrapped
    

    def _default_delivier(self,mode,o_func):
        def default_delivier(self,this_entity,requesting_entity, raw_path, *args,**kwargs):
            match mode:
                case Command.GET:
                    return this_entity.get(requesting_entity, raw_path, *args,**kwargs)
                case Command.PATCH:
                    return this_entity.patch(requesting_entity, raw_path, *args,**kwargs)
                case Command.POST:
                    return this_entity.post(requesting_entity, raw_path, *args,**kwargs)
                case Command.DELETE:
                    return this_entity.delete(requesting_entity, raw_path, *args,**kwargs)
        default_delivier.__name__ = o_func.__name__
        default_delivier.__doc__  = o_func.__doc__
        return default_delivier

    @wraps(_ol_func_item_recieve._wrapper)
    def Get_Recieve(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.GET,*args,**kwargs)

    @wraps(_ol_func_item_recieve._wrapper)
    def Post_Recieve(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.POST,*args,**kwargs)

    @wraps(_ol_func_item_recieve._wrapper)
    def Patch_Recieve(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.PATCH,*args,**kwargs)

    @wraps(_ol_func_item_recieve._wrapper)
    def Delete_Recieve(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.DELETE,*args,**kwargs)


    @wraps(_ol_func_item_deliver._wrapper)
    def Get_Send(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.GET,*args,**kwargs)

    @wraps(_ol_func_item_deliver._wrapper)
    def Post_Send(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.POST,*args,**kwargs)

    @wraps(_ol_func_item_deliver._wrapper)
    def Patch_Send(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.PATCH,*args,**kwargs)

    @wraps(_ol_func_item_deliver._wrapper)
    def Delete_Send(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.DELETE,*args,**kwargs)


    # @wraps(_ol_func_item_recieve._wrapper)
    # def Websocket_Server(self,*args,**kwargs):        
    #     return _ol_func_item_recieve._wrapper(parent=self,mode=Command.DELETE,*args,**kwargs)

    # @wraps(_ol_func_item_deliver._wrapper)
    # def Websocket_Client(self,*args,**kwargs):
    #     return _ol_func_item_deliver._wrapper(parent=self,mode=Command.WEBSOCKET,*args,**kwargs)

    # def Send_Get(self,sending_entity,*args,**kwargs):
    #     return self(Command.GET, sending_entity, *args, **kwargs)
    
    # def Send_Post(self,sending_entity,*args,**kwargs):
    #     return self(Command.POST, sending_entity, *args, **kwargs)
    
    # def Send_Patch(self,sending_entity,*args,**kwargs):
    #     return self(Command.PATCH, sending_entity, *args, **kwargs)
    
    # def Send_Delete(self,sending_entity,*args,**kwargs):
    #     return self(Command.DELETE, sending_entity, *args, **kwargs)


OL_IO = _OL_Container._wrapper


class Foreign_Entity_Base:    
    ''' Foreign Entity Base class, Gives the post commands and ensures formatting on subclasses '''
    def __init_subclass__(cls):
        assert hasattr(cls, '__tablename__' )
        assert hasattr(cls, 'Entity_Type' )
        if cls._interactive:
            assert hasattr(cls, '_Interface'      )
            assert hasattr(cls, 'export_header'   )
            assert hasattr(cls, 'intake_request'  )
            assert hasattr(cls, 'matches_request' )
            assert hasattr(cls, 'export_auth'     )
    is_local      = False
    _interactive  = True
    
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
    def Interface(self):
        t = _CONNECTION_TARGET.set(self)
        yield self._Interface
        _CONNECTION_TARGET.reset(t)

    #TODO: Convert to async requests.

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
        assert hasattr(cls, 'Interface'     )
        assert hasattr(cls, 'export_header' )

    
    def __init__(self):
        t = _INIT_ORIGIN.set(self)
        _OL_Container._on_new(self)
        Interface_Base._on_new(self)
        _INIT_ORIGIN.reset(t)

    def attach_to_app(self, app:FastAPI):
        for v in Interface_Base._iter_insts(self):
            v._register(app)
        return app
    
    def Find_Entity_From_Req(self, request:Request):
        ''' Ensure DB Connection, return foreign item '''
        raise NotImplementedError('Implament in Local_Class!')

class Interface_Base():
    Router_Subpath : str = ''
    _foreign_interface = False
    _origin           = None
    _parent           : Self|Foreign_Entity_Base|Local_Entity_Base

    @property
    def root_entity(self):
        if self._foreign_interface:
            return _CONNECTION_TARGET.get()
        else:
            return self._origin
    
    def __init__(self, parent):
        self._origin = _INIT_ORIGIN.get()
        self._parent = parent
        IO_Websocket._on_new(self)
        _OL_Container._on_new(self)
        Interface_Base._on_new(self)

    @classmethod
    def foreign_platonic(cls):
        ''' Set mode of children to be interface send-only and self.root to get context _CONNECTION_TARGET'''
        inst = cls()
        inst._foreign_interface = True
        return inst

    @staticmethod
    def _on_new(inst, platonic = False):
        ''' Intialize Interface Structure '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if not isclass(v):
                continue
            if issubclass(v,Interface_Base):
                if platonic:
                    setattr(inst,k,v.foreign_platonic(inst))
                else:
                    setattr(inst,k,v(inst))
    
    def _get_raw_path_(self):
        if isinstance(self._parent,(Foreign_Entity_Base,Local_Entity_Base)):
            return ''
        else:
            return self._parent._get_raw_path_() + self.Router_Subpath
    
    @staticmethod
    def _iter_insts(inst):
        ''' Intialize Interface Structure '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if isclass(v) : continue
            if issubclass(v.__class__,Interface_Base): yield v

    def _create_local_router(self):
        return APIRouter()
    
    def _attach_local_router(self,local_router:APIRouter,args=None,kwargs=None):        
        for ol_func in _OL_Container._iter_insts(self):
            ol_func._register(local_router,args,kwargs)
        for websocket in IO_Websocket._iter_insts(self):
            websocket._register(local_router)
        for subinterface in Interface_Base._iter_insts(self):
            subinterface : Self
            subinterface._register(local_router,args,kwargs)
        return local_router
    
    def _register(self, parent_router, args=None, kwargs=None):
        local_router = self._attach_local_router(self._create_local_router(),args,kwargs)
        parent_router.include_router(local_router,prefix = getattr(self,'Router_Subpath', ''))
        return parent_router



if __name__ == '__main__':
    from enum import Enum
    _Example_Entity_Types = Enum(('EXAMPLE',))

    class _example_interface(Interface_Base): 
        ''' Bidirectional interface class, when foreign_platonic it gets contextual connection  '''

        @OL_IO('/test')
        def test(self,foreign_object,data):...

        @test.Post_Send()
        def _test(self, to_entity, from_entity, header):
            ...

    class _example_state(Enum):      ...
    class _example_trust_state(Enum):...

    class _Example_Entity(Local_Entity_Base):
        Entity_Type = _Example_Entity_Types.EXAMPLE
        Interface   = _example_interface
        Connections : Any
        Settings    : Any
            #Database itself

        def export_header(self,target_entity)->dict:
            ''' Exports information about self to be used in the header of a quiry '''
            raise NotImplementedError('EXAMPLE ONLY')    

    class _Example_Foreign_Entity(Foreign_Entity_Base):
        __tablename__ = str(_Example_Entity_Types.EXAMPLE)

        Entity_Type = _Example_Entity_Types.EXAMPLE
        _Interface  = _example_interface.foreign_platonic()

        #Observed & status information
        observed_state  : _example_state
        trust_state     : _example_trust_state
        last_connection : int

        addr     : str
        port     : str
        username : str
        token    : str

        declared_state : _example_state
        
        @contextmanager
        def Interface(self):
            t = _CONNECTION_TARGET.set(self)
            yield self._interface
            _CONNECTION_TARGET.reset(t)

        def export_header(self,target_entity)->dict:
            ''' Exports information about self to be used in the header of a quiry '''
            raise NotImplementedError('EXAMPLE ONLY')

        def matches_header(self,header)->bool:
            ''' See if entity data matches the header '''
            raise NotImplementedError('EXAMPLE ONLY')

        def intake_header(self,header)->None:
            ''' Intakes header to foreign data inst '''
            raise NotImplementedError('EXAMPLE ONLY')


from fastapi   import WebSocket as Server_Websocket, Request, Depends, WebSocketDisconnect, WebSocketException, APIRouter
from inspect   import signature
from functools import partial
from copy      import copy
import websocket as websocket_client
from   websocket import WebSocketApp
import rel

class Event_Pool(dict):
    def __missing__(self,key):
        self[key] = inst = []
        return inst

    def _call_event_manager(self,this_entity, _ext_entity, websocket, args, kwargs, key, *u_args, _extra_callbacks:list = None, **u_kwargs):
        ''' partial-held and called within a websocket process to call events based on key.'''
        res = []
        if _extra_callbacks is None: _extra_callbacks = []
        for event in self[key]:
            res.append(event(this_entity, _ext_entity, websocket, *args,*u_args, **(kwargs|u_kwargs)))
        return res

    def _call_event_client(self,this_entity, _ext_entity, args, kwargs, key, _extra_callbacks:list = None, *u_args, **u_kwargs):
        ''' partial-held and called within a websocket process to call events based on key.'''
        res = []
        if _extra_callbacks is None: _extra_callbacks = []
        for event in (self[key]).extend(_extra_callbacks):
            res.append(event(this_entity, _ext_entity, *args,*u_args, **(kwargs|u_kwargs)))
        return res

class Websocket_Manager(): 
    events : Event_Pool

    def __init__(self, parent):
        self.events = Event_Pool()
        self.parent = parent
    
    custom_run_websocket = None

    def event(self,key):
        ''' Produce a wrapper utilizing a key '''
        def wrapper(func):
            self.events[key].append(func)
            return func
        return wrapper

    def websocket_wrapper(self):
        ''' Produce a wrapped primary-event loop async function for fastapi's wrapper '''
        this_entity  = self.parent._container.root_entity
        ensure_req_entity = this_entity.Find_Entity_From_Req
        
        #May need to be async?
        async def websocket_wrapper(request     : Request             ,
                              websocket   : Server_Websocket          ,
                              _ext_entity = Depends(ensure_req_entity),
                              *args, **kwargs):
             
             close_callback = this_entity.websocket_pool.incoming.attach(websocket, _ext_entity, self.parent)

             res = await self.run_websocket(this_e    = this_entity ,
                                       other_e   = _ext_entity ,
                                       events    = partial(self.events._call_event_manager, this_entity, _ext_entity, websocket, args, kwargs) ,
                                       request   = request     ,
                                       websocket = websocket   ,
                                       *args, **kwargs         )
             close_callback(res)
             return res
        
        if self.custom_run_websocket:
            #Wrap it if there's a custom run func.
            sig = signature(self.custom_run_websocket)
            websocket_wrapper.__name__      = self.custom_run_websocket.__name__
            o_params = signature(websocket_wrapper).parameters
            websocket_wrapper.__signature__ = sig.replace(
                parameters        = [o_params['request'], 
                                     o_params['websocket'], 
                                     o_params['_ext_entity'], 
                                     *list(sig.parameters.values())[3:]], 
                return_annotation = sig.return_annotation )
            
        return websocket_wrapper

    @staticmethod
    async def run_websocket(this_e     : Local_Entity_Base   ,
                            other_e    : Foreign_Entity_Base ,
                            events     : dict                ,
                            request    : Request             ,
                            websocket  : Server_Websocket    ,
                            *args, **kwargs                  ):
        ''' websockets daemon w/ events '''
        events('on_request')
        accept = events('accept_request')
        if len(accept) and (not all(accept)):
            websocket.send_denial_response()
            return
        try:
            await websocket.accept()
            events('on_open')
            while True:
                msg = await websocket.recieve_json()
                events('on_message', msg)
                if any(events('do_close')):
                    websocket.close()
        except WebSocketDisconnect as E:
            events('on_close', E)
        except WebSocketException  as E:
            events('on_error', E) #Placate or raise error?

    def create_router(self,path)->APIRouter:
        local_router = APIRouter()
        local_router.add_api_websocket_route(path, self.websocket_wrapper())
        return local_router

class Websocket_Client(): 
    events : Event_Pool

    def __init__(self, parent):
        self.events = Event_Pool()
        self.parent = parent
    
    custom_run_websocket = None

    def event(self,key):
        ''' Produce a wrapper utilizing a key '''
        def wrapper(func):
            self.events[key].append(func)
            return func
        return wrapper
    
    def default_callbacks_kwargs(self, this_entity, other_entity, _extra_callbacks=None)->dict:
        res = {}
        for key in ['on_request', 'accept_request', 'on_open', 'on_message', 'on_error', 'on_close' ]:
            callback = partial(self.events._call_event_client, this_entity, other_entity, key = key, _extra_callbacks=_extra_callbacks.get(key,[]))                
            res[key] = callback
        return res
    
    def websocket_start_header(self, requesting_entity : 'Local_Entity_Base'):
        ''' handle creation of a websocket & arg injection, plus entity callback '''

        this_entity  = _CONNECTION_TARGET.get()
        other_entity = requesting_entity
        
        raw_path = self.parent._container._get_raw_path_()+'/'+self.parent.path
            #will need to format eventually

        assert issubclass(this_entity.__class__ , Foreign_Entity_Base)
        assert issubclass(other_entity.__class__, Local_Entity_Base  )

        callbacks = self.default_callbacks_kwargs(this_entity,other_entity)
        header = other_entity.export_header | this_entity.export_header()
        
        ws = self.websocket_run(this_entity,other_entity,raw_path,header,callbacks)
        callback = other_entity.websocket_pool.outgoing.attach(ws, this_entity)
        # await ws
        #Not sure if will work
        callback()

    def websocket_run(self,this_entity, other_entity, path, header, callbacks):
        ''' Create and return the app, want to change to be standalone daemon similar to manager. '''
        #websocket_client.WebSocket!! for lower level app creation.
            
        ws = websocket_client.WebSocketApp(path, header = header, **callbacks)
            #TODO: Get rid of this dependency I dont even know will work
        ws.run_forever(dispatcher=rel, reconnect=5)
        return ws
    
    def __call__(self,requesting_entity):
        self.websocket_start_header(requesting_entity)
        
class IO_Websocket():
    manager    : Websocket_Manager
    client     : Websocket_Client
    _container : Interface_Base 

    def __init__(self, path):
        self.manager    = Websocket_Manager(self)
        self.client     = Websocket_Client(self)
        self.path       = path
        self._container = None

    @classmethod
    def _on_new(cls,inst):
        ''' Utility, Call on new item to setup 'views' 
        creates local shallow copies w/ parent fixed '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if isinstance(v,cls):
                if not (v._container is inst): 
                    setattr(inst,k,v._view(inst))

    @staticmethod
    def _iter_insts(inst):
        ''' Intialize Interface Structure '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if isclass(v) : continue
            if issubclass(v.__class__,IO_Websocket): yield v


    def _view(self,container):
        new                = copy(self)
        new._container     = container
        new.manager        = copy(new.manager)
        new.manager.parent = new
        new.client         = copy(new.client)
        new.client.parent  = new
        return new
    
    def _register(self,parent_router:APIRouter):
        parent_router.include_router(self.manager.create_router(self.path))
        return parent_router

    # def __call__(self, other_entity, request=None, *args, **kwargs):
    #     ''' Direct call routing '''
    #     this_entity = self._container.root_entity
    #     recieving = issubclass(this_entity.__class__, Local_Entity_Base)

    #     if recieving:
    #         assert request is not None
    #         return manager.start_websocket(self._container, this_entity, other_entity, *args, **kwargs)

class Websocket_Client_Container():
    ''' Client-Side Websocket Interface, abstracted to be uniform '''
    websocket : WebSocketApp

    def __init__(self,websocket : WebSocketApp, to_entity, from_entity, tags:tuple = tuple()):
        self.websocket     = websocket
        self.entity_type   = to_entity.Entity_Type.value
        self.entity_id     = to_entity.export_identifier()
        self.local_entity  = from_entity
        self.tags          = tags

class Websocket_Manager_Container():
    ''' Manager-Side Websocket Interface, abstracted to be uniform '''
    def __init__(self,websocket : WebSocketApp, to_entity, from_entity, tags:tuple = tuple()):
        self.websocket      = websocket
        self.entity_type    = from_entity.Entity_Type.value
        self.entity_id      = from_entity.export_identifier()
        self.local_entity   = to_entity
        self.tags           = tags

    # def close():
    #     ...    
    # def echo():
    #     ...    
    # def send_json():
    #     ...    

class Websocket_Pool_Slice():
    ''' Filtered bulk_call-iterable-slice yielding from websocket pool base.
    Tags are inclusive '''
    
    def __init__(self,pool:'Websocket_Pool_Base', entity_type=None, entity_id=None, tags=None):
        self.pool = pool
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.tags = tags

    def __iter__(self):
        for socket in self.pool:
            if self.entity_type:
                if not socket.entity_type == self.entity_type:
                    continue
            if self.entity_id:
                if not socket.entity_id == self.entity_id:
                    continue
            if self.tags:
                if not any([x in socket.tags for x in self.tags]):
                    continue
            yield socket

    # def on_ea(self,func_name,*args,**kwargs):
    #     for x in self:
    #         getattr(x,func_name)(*args,**kwargs)
                
class _Websocket_Pool_Base():
    Base = None
    data : list
    
    def __init__(self,      local_entity):
        self.local_entity = local_entity
        self.data   = []

    def attach(self, websocket, to_entity, from_entity, tags)->FunctionType:
        item = self.Base(websocket,to_entity, from_entity, tags)
        self.data.append(item)
        return partial(self.data.remove, item)

    def slice(self,entity_type=None, entity_id=None, tags=None):
        return Websocket_Pool_Slice(self, entity_type=entity_type, entity_id=entity_id, tags=tags)

    def __iter__(self):
        for socket in self.data:
            yield socket

class Websocket_Pool_Outgoing(_Websocket_Pool_Base):
    Base = Websocket_Manager_Container
class Websocket_Pool_Incoming(_Websocket_Pool_Base):
    Base = Websocket_Manager_Container

class Websocket_Pool():
    def __init__(self, entity):
        self.incoming = Websocket_Pool_Incoming(entity)
        self.outgoing = Websocket_Pool_Outgoing(entity)
    
    
