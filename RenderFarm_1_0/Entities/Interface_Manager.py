from fastapi                        import (Request, Response, APIRouter, WebSocket as WebSocketManager)
from starlette.websockets           import WebSocketDisconnect as WebSocketDisconnect_M 
from ws4py.client.threadedclient    import WebSocketClient 

from .EventSystem.Struct_Pub_Sub_v1_2          import Event_Router
from ..Web_Interface.API_V1_8       import (Foreign_Entity_Base, Local_Entity_Base, Interface_Base, IO)
from ..Web_Interface.Websocket_Pool import Manager_Websocket_Wrapper_Simul_Default
from .Websocket_Messsage import make_message, intake_message
import asyncio
from enum import EnumType,Enum
from inspect import isclass
from copy import copy


class Websocket_State_Info(Manager_Websocket_Wrapper_Simul_Default):
    Events = Event_Router.New()
    events = None

    local_entity   : 'Manager_Local'
    foreign_entity : 'UNDEC_Foreign'

    async def pre_run(self, buffer_tick_rate = 2):
        self.buffer = []
        self.buffer_tick_rate = buffer_tick_rate
        self.start_populate_buffer()
        if not self.events:
            self.events = self.Events(self)
        self.events_callback = self.local_entity.events.temp_attach_router_inst(self.events)

    def after(self,):
        self.events_callback()
    
    def make_simul_tasks(self,):
        ''' Re-creates tasks on each completion
        TODO: Instead optionally make bellow a factory to re-queue each indv automatically '''
        
        return [
            asyncio.create_task(self.send_buffer()),
            asyncio.create_task(self.receive_json()),
        ]

    async def send_buffer(self):
        while True:
            if len(self.buffer):
                buffer = copy(self.buffer)
                self.buffer.clear()
                for x in buffer:
                    await self.websocket.send_json(x)
            await asyncio.sleep(self.buffer_tick_rate)

    async def receive_json(self):
        val = await self.websocket.receive_json()
        print('Got Val:', val)

    def start_populate_buffer(self,):
        from .Entity_Declaration import Worker_Foreign,UNDEC_Foreign,Manager_Foreign,Client_Foreign
            #bad practice, this indicates a structural issue. consider splitting Foreign to secondary file

        self.buffer.extend([
            make_message(None, 'CRUD', 'BULK_CREATE', ['workers'   , self.gather_intial_send(self.local_entity.client_db_session, Worker_Foreign  , ['uid','host','port','con_state','action_state'])] ),
            make_message(None, 'CRUD', 'BULK_CREATE', ['UNDECLARED', self.gather_intial_send(self.local_entity.client_db_session, UNDEC_Foreign   , ['uid','host','port','con_state','action_state'])] ), #|self.gather_all_clients()
            make_message(None, 'CRUD', 'BULK_CREATE', ['managers'  , self.gather_intial_send(self.local_entity.client_db_session, Manager_Foreign , ['uid','host','port','con_state','action_state'])] ),
            make_message(None, 'CRUD', 'BULK_CREATE', ['clients'   , self.gather_intial_send(self.local_entity.client_db_session, Client_Foreign  , ['uid','host','port','con_state','action_state'])] ), #|self.gather_all_clients()
            # ('BULK_CREATE','jobs',    self.gather_all_jobs( this_e.))
        ])

        print(self.buffer)


    def gather_intial_send(self, session, table, attrs):
        res = []
        for row in session.query(table).all():
            res.append(self.gather_item(row,attrs))
        return res

    def gather_item(self,row, attrs):
        item = {}
        for attr in attrs:
            val = getattr(row, attr, None)
            if issubclass(val.__class__,Enum):
                item[attr] = val.value
            else:
                item[attr] = val
        return item

    @Events.Sub('after_insert')
    def insert_client(self, event, event_key, container, mapper, connection):
        self.buffer.append(make_message(None, 'CRUD', 'CREATE', [container.__tablename__, self.gather_item(container, ['uid','host','port','con_state','action_state'])] ),)

    @Events.Sub('after_update')
    def update_client(self, event, event_key, container, mapper, connection):
        self.buffer.append(make_message(None, 'CRUD', 'UPDATE', [container.__tablename__, self.gather_item(container, ['uid','host','port','con_state','action_state'])] ),)

    @Events.Sub('after_delete')
    def delete_client(self, event, event_key, container, mapper, connection):
        self.buffer.append(make_message(None, 'CRUD', 'DELETE', [container.__tablename__, self.gather_item(container, ['uid','host','port','con_state','action_state'])] ),)
    
class Manager_Interface_Info(Interface_Base):
    router = APIRouter()
    @IO.Get(router,'/')
    def base_page(self, this_e, other_e, req, ):
        return this_e.fapi_mg_templates.TemplateResponse(
            "/info/info1.html",
            {   'request' : req, 
                'Manager_Name':this_e.settings.label},
        )

    @IO.Websocket(router,'/state-info')
    async def state_info(self, this_e, other_e, websocket:WebSocketManager):
                
        ws = Websocket_State_Info(this_e, other_e, websocket, 'state_info')
        await ws.accept()
        try:
            await ws.run_handler()
        except WebSocketDisconnect_M:
            print('REACHED WEBSOCKET DISCON')
            await ws.close()


    @IO.Get(router,'/tests/testa')
    def test_a(self, this_e, other_e, req,):
        return True

    @IO.Get(router,'/tests/testb')
    def test_b(self, this_e, other_e, req,):
        dp = this_e.settings._test_upload_files.data
        from .FileDB.FileHashing import uuid_utils
        
        struct = uuid_utils.create_structure(dp)
        struct.calculate_file_hashes()
        return struct._export_struct_()

    @IO.Get(router,'/tests/testc')
    def test_c(self, this_e, other_e, req,):
        dp = this_e.settings._test_upload_files.data
        from .FileDB.FileHashing import uuid_utils
        
        struct = uuid_utils.create_structure(dp)
        from .FileDB.db_struct import File,Space,asc_Space_NamedFile, asc_Space_NamedSpace
        allrows = this_e.file_db_session.query
        all_hashes = [x.id for x in [*allrows(File),*allrows(Space),*allrows(asc_Space_NamedFile),*allrows(asc_Space_NamedSpace)]]

        
        struct.calculate_file_hashes()
        
        ignored_fr_db    = struct._export_struct_(ignore_hashes = all_hashes)
        ignored_fr_first = struct._export_struct_(ignore_hashes = [struct.data_hash])
        return {
            'ignored_fr_db' : ignored_fr_db,
            'ignored_fr_first' : ignored_fr_first,
        }

    @IO.Get(router,'/tests/testd')
    def test_d(self, this_e, other_e, req,):
        dp = this_e.settings._test_upload_files.data
        from .FileDB.FileHashing import uuid_utils
        
        struct = uuid_utils.create_structure(dp)        
        struct.calculate_file_hashes()
        from .Interface_FileDB import header_interface

        from .FileDB.db_struct import File,Space,asc_Space_NamedFile, asc_Space_NamedSpace
        
        unheld = header_interface.diff_future(struct.get_file_datahash_list(),[])
        return unheld

                
        
    



class Manager_Worker_Interface(Interface_Base):
    ...
#     router = APIRouter()
    
#     @IO.Get(router,'/test')
#     def test(self, this_e, other_e, req):
#         return True

#     @IO.Websocket(router,'/ws')
#     async def worker_websocket(self, this_e, other_e, websocket:WebSocketManager):
#         from starlette.websockets import WebSocketDisconnect,WebSocketClose
#         await websocket.accept()
#         await websocket.send_text('Hello')
#         await websocket.close()
#     @worker_websocket.Client()
#     async def worker_websocketclient(self,this_e:Foreign_Entity_Base, other_e:Local_Entity_Base, path, headers):

#         class custom_ws_class(WebSocketClient):
#             def opened(self):
#                 pool = other_e.client_websocket_pool
#                 pool.attach(other_e, this_e, self,self.__class__.__name__)
#                 self.send('GREETINGS!')
#                 # self.close()
                
#             def closed(self, code, reason=None):
#                 pool = other_e.client_websocket_pool
#                 pool.remove(self)
#                 print('WEBSOCKET CLOSED!')
            
#             def received_message(self, message):
#                 print('RECEIVED MESSAGE:', message)
#                 self.send('GOODBYE!')
#                 self.close()
            
#             async def run_forever(self):
#                 return super().run_forever()

#         fullpath = f'ws://{this_e.host}:{this_e.port}' + path
#         print(fullpath)

#         ws = custom_ws_class(fullpath, headers=headers.items())
#         try:
#             ws.connect()
#             asyncio.create_task(ws.run_forever())
#             return ws
#         except Exception as e:
#             print(f'Cound not connect! Reason: {e}')
#             return None