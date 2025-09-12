from types     import FunctionType
from typing    import Any
from functools import partial, wraps
from inspect   import isclass
from ws4py.client.threadedclient import WebSocketClient as Websocket_Client
from starlette.websockets        import WebSocket       as Websocket_Manager
from starlette.websockets        import WebSocketDisconnect
from .API_V1_8 import Local_Entity_Base, Foreign_Entity_Base




class Websocket_Pool_Slice():
    ''' Filter object, short or long-lived. Corrisponds to active state in con pool '''

    def __init__(self, parent:'Websocket_Pool_Base', filter: FunctionType):
        self.parent = parent
        self.filter = filter
    
    @property
    def data(self):
        for x in self.parent:
            if self.filter(x):
                yield x

    def __iter__(self):
        for ws in self.data:
            yield ws

    def __len__(self):
        return len(list(self.data))

class Websocket_View():
    id                :str
    uid               :str
    foreign_entity_id :str|Any

    def __init__(self, websocket, entity_type, foreign_entity_id, id=None, uid=None):
        self.websocket = websocket
        self.entity_type = entity_type
        self.foreign_entity_id = foreign_entity_id
        self.id  = id
        self.uid = uid
    
    def __getattr__(self,key):
        if not key in dir(self):
            return getattr(self.websocket.key)


class Websocket_Pool_Base():
    Base_Type = ...
    data      = list[Websocket_View]

    def __init__(self):
        self.data = []

    def __iter__(self):
        for x in self.data:
            yield x
        
    def attach(self, local_entity:Local_Entity_Base, foreign_entity:Foreign_Entity_Base, ws_item, id, uid=None, return_existing_matching_uid=False)->None:
        ''' Attach to self.data and asc with id, uid. if UID, enforce active per-entity singleton '''
        print(ws_item)
        assert issubclass(ws_item.__class__, self.Base_Type)
        if uid is not None:
            by_id = list(self.slice(foreign_entity.Entity_Type.value, foreign_entity.id, id = Any, uid = uid))
            if return_existing_matching_uid and by_id:
                assert len(by_id) == 1
                return by_id[0]
            elif by_id:
                raise Exception('COLLIDING WS-UID UNDER {foreign_entity.Entity_Type.value}:{foreign_entity.id}: {uid}}!')
        view = Websocket_View(ws_item, foreign_entity.Entity_Type, foreign_entity.id, id, uid)
        self.data.append(view)
        return partial(self.data.remove,view)

    def remove(self, websocket : Websocket_Client|Websocket_Manager|Websocket_View|Websocket_Pool_Slice):
        ''' Typically on closing, remove from data if item is still in self.data '''
        
        if issubclass(websocket.__class__, self.Base_Type):
            return self._remove_by_base(websocket) 
        elif isinstance(websocket, Websocket_View):
            return self._remove_by_view(websocket)
        elif isinstance(websocket, Websocket_Pool_Slice):
            return self._remove_by_slice(websocket)
        
    def _remove_by_base(self, ws_item: Websocket_Manager|Websocket_Client):
        rem = []
        for x in self.data:
            if x.websocket is ws_item:
                rem.append(x)
        for x in rem:
            self.data.remove(x)

    def _remove_by_view(self, view:Websocket_View):
        if view in self.data:
            self.data.remove(view)

    def _remove_by_slice(self, slice:Websocket_Pool_Slice):
        rem = []
        for x in slice:
            if x in self.data:
                self.data.remove(x)

    def slice(self, entity_type:str=None, foreign_entity_id:str|None=None, id:str|None=Any, uid:str|None=Any):
        return Websocket_Pool_Slice(self, filter = partial(self._filter, entity_type=entity_type, foreign_entity_id=foreign_entity_id, id=id, uid=uid))

    def _filter(self, websocket : Websocket_View, entity_type:str|None=Any, foreign_entity_id:str|None=None, id:str|None=Any, uid:str|None=Any ) -> bool:
        return all([
            self._atomic_filter(websocket.entity_type, entity_type)    ,
            self._atomic_filter(websocket.foreign_entity_id, foreign_entity_id),
            self._atomic_filter(websocket.id, id)    ,
            self._atomic_filter(websocket.uid, uid)  ,])
        
    @staticmethod
    def _atomic_filter(base,check_value):
        if check_value is Any:
            return True
        
        elif check_value is None:
            return not base
        
        elif check_value is FunctionType:
            return check_value(base)
        
        elif isclass(base):
            return base is check_value #ie if enum
        
        elif hasattr(check_value,'__iter__') and not (hasattr(base,'__iter__')):
            return base in check_value
        
        return base == check_value

import asyncio

class Manager_Websocket_Wrapper_Base():
    websocket:Websocket_Manager
    def __init__(self,local_entity, foreign_entity, websocket, id, uid=None):
        self.local_entity = local_entity
        self.foreign_entity = foreign_entity
        self.websocket = websocket
        self.id  = id
        self.uid = uid

    async def accept(self):
        await self.websocket.accept()
        pool = self.local_entity.manager_websocket_pool
        pool : Manager_Websocket_Pool
        self.close_callback = pool.attach(self.local_entity, self.foreign_entity, self,  self.id, self.uid)
        
    async def run_handler(self,*args,**kwargs):
        task = asyncio.create_task(self.run_wrapper(*args,**kwargs))
        self.current_task = task
        return await task
    
    async def run_wrapper(self,*args,**kwargs):
        self.continue_execution = True
        gen = self.run(*args, **kwargs)
        async for x in gen:
            if self.websocket.client_state.name != 'CONNECTED': await gen.aclose(); break
            if not self.continue_execution: await gen.aclose(); break

    async def close(self):
        self.continue_execution = False
        if self.current_task:
            try: await self.current_task
            except WebSocketDisconnect: ...
        if self.close_callback:
            self.close_callback()
        # await self.current_task

    async def run(self):
        raise Exception('DEFINE ON CHILD CLASS')

class Manager_Websocket_Wrapper_Simul_Default(Manager_Websocket_Wrapper_Base):
    # Tick_Rate = 1
    
    async def recieve_json(self):
        res = await self.websocket.recieve_json()
        print(res)

    def make_simul_tasks(self):
        return [
            asyncio.create_task(self.recieve_json())
            # asyncio.create_task(self.websocket.recieve_json())
                #At least one send or recieve is required for disconnect to be raised!!
                #Can attach callbacks here as well
        ]
    
    def after(self):
        ...
    def on_discon(self):
        ...
    def on_stopasync(self):
        ...

    async def run(self,*args,**kwargs):
        self.pre_run(*args,**kwargs)
        try:
            while True:
                # wait = asyncio.create_task(asyncio.sleep(self.Tick_Rate))
                complete, pending = await asyncio.wait(self.make_simul_tasks(), return_when=asyncio.FIRST_COMPLETED) 
                for x in pending:
                    x.cancel()
                for c in complete:
                    if e:=c.exception():
                        raise e
                yield   
        except WebSocketDisconnect:
            # print('HIT WebSocketDisconnect')
            self.on_discon()
            self.after()
            raise
        except StopAsyncIteration:
            self.on_stopasync()
            self.after()
        finally:
            ...
            #Actionitive code here
    
    async def pre_run(self,*args,**kwargs):
        ...

class Manager_Websocket_Pool(Websocket_Pool_Base):
    Base_Type = Manager_Websocket_Wrapper_Base
class Client_Websocket_Pool(Websocket_Pool_Base):
    Base_Type = Websocket_Client