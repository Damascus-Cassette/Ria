
from sqlalchemy     import (Column              ,
                            Boolean             ,
                            Integer             ,
                            String              ,
                            create_engine       ,
                            Engine as EngineType)

from sqlalchemy.orm import (declarative_base    , 
                            sessionmaker        , 
                            Session as SessionType)

from .API_V1_8      import (IO                  ,
                            Interface_Base      ,
                            Foreign_Entity_Base ,
                            Local_Entity_Base   )


from fastapi        import (Request                       ,
                            APIRouter                     ,
                            WebSocket as WebSocket_Manager)

# from websocket      import (WebSocket    as Websocket_Client   ,
#                             WebSocketApp as WebsocketApp_Client)

from .Websocket_Pool import (Manager_Websocket_Pool, 
                             Client_Websocket_Pool,
                             Manager_Websocket_Wrapper_Base,)

from ws4py.client.threadedclient import WebSocketClient 

from enum import Enum
from fastapi.responses import HTMLResponse

DB_Base = declarative_base()



_test_html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://127.0.0.1:4000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""
#FROM EXAMPLE: https://fastapi.tiangolo.com/advanced/websockets/#in-production 


class Entity_Types(Enum):
    A     = 'A'
    B     = 'B'
    UNDEC = 'UNDEC'

class UNDEC_Foreign(Foreign_Entity_Base,DB_Base):
    __tablename__ = Entity_Types.UNDEC.value 
    _interactive  = False
    Entity_Type   = Entity_Types.UNDEC

    def __init__(self,host,port):
        self.host = host
        self.port = port
        # self.id  = host + ':' +port

    id  = Column(Integer, primary_key=True)
    host = Column(String)
    port = Column(String)

    @property
    def unique_id(self):
        return self.id

    def __repr__(self):
        return f'< {self.Entity_Type} | {self.host}:{self.port} @ row {self.id} > '

    def matches_request(self, request:Request, headers:Request.headers):
        return all([
            str(self.host) == str(request.client.host),
            # str(self.port) == str(request.client.port),
        ])

    def intake_request(self, request:Request, headers:Request.headers):
        self.host = request.client.host
        self.port = request.client.port
    
    @classmethod
    def New_From_Request(cls, local_entity, request):
        return cls(request.headers.get('UID'), request.client.host, request.client.port)


class AB_Interface(Interface_Base):
    router1 = APIRouter()
    
    @IO.Get(router1,'/test')
    def test(self, this_e, other_e, request,)->str:
        # print('GOT REQUEST:', this_e,other_e,request)
        return 'GET Test_Success'

    # @test.Send()
    # def _test(this_e, other_e, raw_path):
    #     return this_e.get(other_e, raw_path)
    @IO.Get(router1,'/current_test')
    async def test_0(self, this_e, other_e, request)->dict:
        res = {}
        for con_entity in this_e.connections(B_Foreign):
            res[con_entity.Entity_Type.value] = data = []
            with con_entity.Active():
                con = await con_entity.interface.test_8b()
                print(con)
                # data.append()
        return res

    @IO.Get(router1,'/path/{msg}')
    def test_1(self, this_e, other_e, request, msg=''):
        return f'GET Test_Success : {msg}'

    @IO.Get(router1,'/reflect')
    def test_2(self, this_e, other_e, request):
        print(f'INSIDE /reflect, {this_e} {other_e}, {request}')
        return f'GET /reflect from {other_e} -> {this_e}'

    @IO.Get(router1,'/reflect_on_entities')
    def test_3(self, this_e, other_e, request)->dict:
        res = {}

        for con_entity in this_e.connections(B_Foreign):
            res[con_entity.Entity_Type.value] = data = []
            with con_entity.Active():
                data.append(con_entity.interface.test_2(data ='HELLO'))
        return res
    
    @IO.Post(router1,'/test')
    def test_4(self, this_e, other_e, request, data)->str:
        print(f'DATA IS {data}')
        return f'SUCESS IN POST: {data}'

    @IO.Delete(router1,'/test')
    def test_5(self, this_e, other_e, request, data)->str:
        return f'SUCESS IN DELETE: {data}'

    @IO.Patch(router1,'/test')
    def test_6(self, this_e, other_e, request, data)->str:
        return f'SUCESS IN PATCH: {data}'

    @IO.Put(router1,'/test')
    def test_7(self, this_e, other_e, request, data)->str:
        return f'SUCESS IN Put: {data}'
        
    @IO.Get(router1,'/ws_test')
    def test_8a(self, this_e, other_e, request)->str:
        return HTMLResponse(_test_html)
    
    @IO.Websocket(router1,'/ws')
    async def test_8b(self, this_e, other_e, websocket:WebSocket_Manager)->str:
        ''' Local of example of https://fastapi.tiangolo.com/advanced/websockets/#in-production '''

        class custom_ws_class(Manager_Websocket_Wrapper_Base):
            async def run(self):
                await self.accept()
                while True:
                    data = await self.receive_text()
                    print(data)
                    await self.send_text(f"Message text was: {data}")
                    # await self.send_text(str(self.this_entity.websocket_as_manager_pool))
                    if data == 'CLOSE':
                        break
                await self.send_text(f"CLOSING CONNECTION")
                await self.close()

        app = custom_ws_class(this_e, other_e, websocket, id = 'test_connection', uid = 'single_test' )        

        return await app.run_with_handler()
        # Consider using asyncio.gather or similar for above.

    @test_8b.Client()
    async def test_8c(self, this_e:Foreign_Entity_Base, other_e:Local_Entity_Base, path, headers,):
        
        class custom_ws_class(WebSocketClient):
            def opened(self):
                pool = other_e.client_websocket_pool
                pool.attach(other_e, this_e, self,self.__class__.__name__)
                self.send('GREETINGS!')

            def closed(self, code, reason=None):
                pool = other_e.client_websocket_pool
                pool.remove(self)
            
            def received_message(self, message):
                print('RECEIVED MESSAGE:', message)
                self.send('GOODBYE!')
                self.close()

        ws = custom_ws_class(f'ws://{this_e.host}:{this_e.port}' + path, headers=headers.items())
        ws.connect()
        ws.run_forever()
        return ws
        



    # @test.Send()
    # def _test(this_e, other_e,raw_path, msg):
    #     return this_e.get(other_e, raw_path, msg=msg)

    
    
class A_Local(Local_Entity_Base):
    Entity_Type = Entity_Types.A
    interface = AB_Interface

    def __init__(self, unique_id, db_url):
        super().__init__()
        self.unique_id = unique_id

        self.manager_websocket_pool = Manager_Websocket_Pool()
        self.client_websocket_pool  = Client_Websocket_Pool()
        # self.websocket_pool = Websocket_Pool(self)

        self.db_url  = db_url
        self.engine  = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        DB_Base.metadata.create_all(self.engine)

    db_url  : str
    engine  : EngineType
    Session : SessionType #Base Type
    session : SessionType #Instance

    def export_header(self, to_entity:Foreign_Entity_Base)->dict:
        return {'Role': self.Entity_Type.value, 
                'UID' : self.unique_id}

    async def Find_Entity_From_Req(self, request:Request):
        ''' Ensure DB Connection, return foreign item '''
        if incoming_role:=request.headers.get('role'):
            table = ROLE_TABLE_MAPPING[incoming_role]
            print('GOT ROLE:', incoming_role)
        else:
            table = UNDEC_Foreign
        rows = self.session.query(table).all()
        for row in rows:
            if row.matches_request(request, request.headers):
                row.intake_request(request, request.headers)
                self.session.commit()
                return row
            
        new_row = table.New_From_Request(self,request)
        self.session.add(new_row)
        self.session.commit()
        return new_row

    async def Find_Entity_From_WsReq(self, websocket:WebSocket_Manager):
        ''' Ensure DB Connection, return foreign item '''
        return await self.Find_Entity_From_Req(websocket)
    
    def connections(self, table_types:Foreign_Entity_Base=None):
        if table_types is None: table_types = list(ROLE_TABLE_MAPPING.values())
        elif not isinstance(table_types,(list,tuple)): table_types = [table_types]
        for table in table_types:
            assert issubclass(table, Foreign_Entity_Base)
            rows = self.session.query(table).all()
            for other_entity in rows:
                yield other_entity

class A_Foreign(Foreign_Entity_Base, DB_Base):
    __tablename__ = Entity_Types.A.value + '_Entity'
    Entity_Type   = Entity_Types.A
    interface     = AB_Interface()
    
    def __repr__(self):
        return f'< {self.Entity_Type} | {self.host}:{self.port} @ row {self.id} > '

    def __init__(self,unqiue_id,host,port):
        self.id = unqiue_id
        self.host = host
        self.port = port
        # self.id  = host + ':' +port

    id   = Column(String, primary_key=True)
    host = Column(String)
    port = Column(String)

    def export_header(self, from_entity:Local_Entity_Base)->dict:
        return {}
    
    def intake_request(self, request, header):
        self.port = request.client.port
        self.host = request.client.host
        
    def matches_request(self,request:Request, headers:Request.headers):
        return all([headers.get('Role', default = '') == self.Entity_Type.value,
                    headers.get('UID',  default = '') == self.id])

    def export_auth(self,from_entity)->tuple:
        return tuple()
    
    @classmethod
    def New_From_Request(cls,local_entity, request):
        return cls(request.headers.get('UID'), request.client.host, request.client.port)
    
class B_Local(A_Local):
    Entity_Type   = Entity_Types.B 

class B_Foreign(Foreign_Entity_Base, DB_Base):
    __tablename__ = Entity_Types.B.value + '_Entity'
    Entity_Type   = Entity_Types.B 
    interface     = AB_Interface()
    

    def __repr__(self):
        return f'< {self.Entity_Type} | {self.host}:{self.port} @ row {self.id} > '
    def __init__(self,unqiue_id,host,port):
        self.id = unqiue_id
        self.host = host
        self.port = port
        # self.id  = host + ':' +port

    id   = Column(String, primary_key=True)
    host = Column(String)
    port = Column(String)

    def export_header(self, from_entity:Local_Entity_Base)->dict:
        return {}
    
    def intake_request(self, request, header):
        # self.port = header.get('port', default = '----')
        # self.host = header.get('host', default = '----')
        self.port = request.client.port
        self.host = request.client.host
        
    def matches_request(self,request:Request, headers:Request.headers):
        return all([headers.get('Role', default = '') == self.Entity_Type.value,
                    headers.get('UID',  default = '') == self.id])

    def export_auth(self,from_entity)->tuple:
        return tuple()

ROLE_TABLE_MAPPING = {
    A_Foreign.Entity_Type.value : A_Foreign,
    B_Foreign.Entity_Type.value : B_Foreign,
}


from fastapi import FastAPI

db_url = 'sqlite:///database_A.db'
inst_a = A_Local('TestEntityA',db_url)
inst_a.session.merge(B_Foreign(
    unqiue_id = 'TestEntityB',
    host = '127.0.0.1',
    port = '4001',
))
inst_a.session.commit()
app_a  = inst_a.attach_to_app(FastAPI())


db_url = 'sqlite:///database_B.db'
inst_b = B_Local('TestEntityB',db_url)
inst_b.session.merge(A_Foreign(
    unqiue_id= 'TestEntityA',
    host = '127.0.0.1',
    port = '4000',
))
inst_b.session.commit()
app_b  = inst_b.attach_to_app(FastAPI())

@app_a.get("/url-list")
def get_all_urls():
    url_list = [{"path": route.path, "name": route.name} for route in app_a.routes]
    return url_list
@app_b.get("/url-list")
def get_all_urls():
    url_list = [{"path": route.path, "name": route.name} for route in app_b.routes]
    return url_list

#python -m uvicorn Web_Interface.API_V1_8_test:app_a --port 4000 --reload
#python -m uvicorn Web_Interface.API_V1_8_test:app_b --port 4001 --reload

