
from .API_V1_7 import Interface_Base, Local_Entity_Base, Foreign_Entity_Base,_CONNECTION_TARGET

from fastapi   import WebSocket as Server_Websocket, Request, Depends, WebSocketDisconnect, WebSocketException, APIRouter
from inspect   import signature
from functools import partial
from copy      import copy
import websocket as websocket_client
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
    
    async def websocket_start_header(self):
        ''' handle creation of a websocket & arg injection, plus entity callback '''
        this_entity  = self.parent._container.root_entity
        other_entity = _CONNECTION_TARGET.get()
        
        path = self.parent._container._get_raw_path_()+'/'+self.parent.path

        assert issubclass(this_entity.__class__ ,Foreign_Entity_Base)
        assert issubclass(other_entity.__class__,Local_Entity_Base  )
        callbacks = self.default_callbacks_kwargs(this_entity,other_entity)
        header = other_entity.export_header | this_entity.export_header()
        ws = self.run(this_entity,other_entity,path,header,callbacks)
        
        callback = other_entity.websocket_pool.outgoing.attach(ws, this_entity)
        
        await ws
        callback()

    def run(self,this_entity, other_entity, path, header, callbacks):
        ws = websocket_client.WebSocketApp(path, header = header, **callbacks)
            #TODO: Get rid of this dependency I dont even know will work
        ws.run_forever(dispatcher=rel, reconnect=5)
        return ws
    
        


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

    def _view(self,container):
        new                = copy(self)
        new._container     = container
        new.manager        = copy(new.manager)
        new.manager.parent = self
        new.client         = copy(new.client)
        new.client.parent  = self
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
