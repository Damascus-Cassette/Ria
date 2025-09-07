
class Events_Dict(dict):
    def __missing__(self,key):
        self[key] = inst = []
        return []

    def run(self,event_key:str, *args, **kwargs):
        res = []
        for x in self[event_key]:
            res.append(x(*args,**kwargs))
        return res

class Websocket_Manager():
    
    def __init__(self, parent:'IO_websocket'):
        self.fapi_args   = []
        self.fapi_kwargs = {}
        self.events = Events_Dict()
    
    # def _register(self,router):
    #     router = self.create_router()
    #     self.router.include_route(router)
        #Add wrapper function of self somewhere here
    
    def create_router(self):
        self.create_wrapper()
        return fastapi.router(*self.fapi_args, *self.fapi_kwargs)

    def fapi_args(self,*args, **kwargs):
        self.fapi_args = args
        self.fapi_kwargs = kwargs
        
    def on_request(self): return self._event_wrapper('on_request')
    def on_request(self): return self._event_wrapper('accept_request')
    def on_open(self):    return self._event_wrapper('on_open')
    def on_message(self): return self._event_wrapper('on_message')
    def on_error(self):   return self._event_wrapper('on_error')
    def on_close(self):   return self._event_wrapper('on_close')

    def _event_wrapper(self,event:str):
        def wrapper(func):
            self.events[event] = func
            return func
        return wrapper
        
    def custom(self):
        def wrapper(func):
            self.custom_start = func
            return func
        return wrapper
    
    custom_start = None
    async def start_ws(self, event, this_entity, other_entity, request, websocket, *args,**kwargs):
        ''' Create and call websockets daemon w/ events. Can be overriden '''
        event('on_request')
        if not all(event('accept_request')):
            websocket.reject()
        websocket.accept()
        event('on_open')
        try:
            while True:
                msg = await websocket.recieve_json()
                event('on_message', msg)
                if any(event('do_close')):
                    websocket.close()
        except WebSocketDisconnect as E:
            event('on_close', E)
        except Exception as E:
            event('on_error', E)
        
    def __call__(self,container)->websocket:
        #Prep call for start_ws and return the ws
        ...
        
class Websocket_Client():
    
    def __init__(self, parent:'IO_websocket'):
        self.events = Events_Dict()
        self.args   = []
        self.kwargs = []
    
    def on_request(self): return self._event_wrapper('on_request')
    def on_request(self): return self._event_wrapper('accept_request')
    def on_open(self):    return self._event_wrapper('on_open')
    def on_message(self): return self._event_wrapper('on_message')
    def on_error(self):   return self._event_wrapper('on_error')
    def on_close(self):   return self._event_wrapper('on_close')


    def create_callback(self,event_key, *inserted_args,**inserted_kwargs):
        def func(*args,**kwargs):
            res = []
            for event in self.events[event_key]:
                res.append(event(*inserted_args,*args,**(inserted_kwargs|kwargs)))
            return res
        return func
    
    def default_callbacks_kwargs(self)->dict:
        res = {}
        for key in ['on_request', 'accept_request', 'on_open', 'on_message', 'on_error', 'on_close' ]:
            res[key] = self.create_callback()
        return res

    def _event_wrapper(self,event:str):
        def wrapper(func):
            self.events[event] = func
            return func
        return wrapper

    def custom(self):
        def wrapper(func):
            self.custom_start = func
            return func
        return wrapper
    
    custom_start = None
    def start_ws(self, this_e:'local_entity', other_e:'foreign_entity', path:str):
        header    = other_e.export_header() | this_e.export_header()
        callbacks = self.create_callback(this_e,other_e)

        ws = websocket.WebSocketApp(path, header = header, **callbacks)
        ws.run_forever(dispatcher=rel, reconnect=5)

        other_e.ws_pool.append(ws)


    def __call__(self, container):
        if self.custom_start:
        #Start websocket and insert entities and path
        #create callbacks to insert as well
        ...


class IO_websocket():
    client  : Websocket_Client
    manager : Websocket_Manager

    def __init__(self, path, limit = 1, limit_by_tag = True, limit_by_path = True, tag=None, con_retry = 5, con_fail = -1):
        #Connection retry and fail
        #Limit should be one per tag per tentity
        self.client  = Websocket_Client (self)
        self.manager = Websocket_Manager(self)
    
    def __get__(self,inst,inst_cls)->Websocket_Manager|Websocket_Client:
        ''' Return relative client or manager class.'''
        if inst is None:
            if inst.is_local:
                return partial(self.manager, inst)
            else:
                return partial(self.worker, inst)
        return self
    
    def create_router(self,*args,**kwargs):
        ''' Not accessable when the parent is an inst, so this is a hack'''
        return self.manager.create_router(self.path,*args,**kwargs)

        
        

class interface_example():
    con_test = IO_websocket('/path/{arg}')
    router   = con_test.create_router()#fapi_arg,fapi_kwargs)
    #change itnerface to pickup all routers
    
    # @con_test.manager.custom()
    # async def _manager(self, this_e:'local_entity', other_e:'foriegn_entity', events, request, websocket,path_kwargs)->websocket:
    #     '''Custom primary loop '''
    @con_test.manager.accept_request()
    def _manager_open(self, manager_inst:Websocket_Manager, this_e,other_e,request,websocket,path_kwargs):
        ''' Gate Websocket '''
        return True

    @con_test.manager.on_error()
    def _manager_on_error(self,this_e, other_e, request, websocket,error,path_kwargs):
        ''' Error handler function, websocket can be closed from here. Close error with be caught '''

    # @con_test.client.custom()
    # def _client(self, client_inst:Websocket_Client, this_e, other_e, path, arg=None)->websocket: #Provided, then passed up?
    #     ''' Custom decalartion and start of websocket-client.WebsocketApp'''

    @con_test.client.on_close()
    def _client_open(self,this_e, other_e, ):
        ...

class manager_interface():
    con_test          = IO_websocket('/path/{arg}')
    con_test_router   = con_test.create_router()

    @con_test.manager.on_open()
    async def _manager_on_open(self, this_e, other_e, websocket,arg):
        return await websocket.send_json(this_e.source_data)
    


class Ws_Pool():
    # Pool of connections by foreign object type, instance, tag | path
    # Each return is a con_pool_slice object with the parameters argued & reference to master.
    # when atttaching to a slice, the con takes on the params of the slice.
    # Should be held on the local object.
    ...


# CON_POOL = Ws_Pool()

class foreign_object():
    _interface = interface_example 
    # ws_pool    = CON_POOL.getter()

    # def __init__():
    #     ws_pool = ws_pool() # Should be connection manager per entity. I should take a systems approach and broadcast to same key streams per, and allowing limiting ws connections
    #     #Cant be directly on foreign object! Sqlalachemy re-generates class per req
