
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

from websocket      import (WebSocket    as Websocket_Client   ,
                            WebSocketApp as WebsocketApp_Client)
from enum import Enum

DB_Base = declarative_base()



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

    def __repr__(self):
        return f'< {self.Entity_Type} | {self.host}:{self.port} @ row {self.id} > '

    def matches_request(self, request:Request, headers:Request.headers):
        return all([
            str(self.host) == str(request.client.host),
            # str(self.port) == str(request.client.port),
        ])

    def intake_request(self, request:Request, headers:Request.headers):
        self.port = request.client.port
        
    
    @classmethod
    def New_From_Request(cls, request):
        return cls(request.client.host, request.client.port)


class AB_Interface(Interface_Base):
    router1 = APIRouter()
    
    @IO.Get(router1,'/test')
    def test(self, this_e, other_e, request,)->str:
        # print('GOT REQUEST:', this_e,other_e,request)
        return 'GET Test_Success'

    # @test.Send()
    # def _test(this_e, other_e, raw_path):
    #     return this_e.get(other_e, raw_path)

    @IO.Get(router1,'/path/{msg}')
    def test_1(self, this_e, other_e, request, msg=''):
        return f'GET Test_Success : {msg}'
    # @test.Send()
    # def _test(this_e, other_e,raw_path, msg):
    #     return this_e.get(other_e, raw_path, msg=msg)

    
    # @IO.Get(router1,'/ws_listen')
    # def ws_listen(self, this_e, other_e, request):
    #     ''' list all current connections? '''

    # websocket_test = IO.Websocket(router1,'/websocket')
    
    # # @websocket_test.manager.custom_app('on_load')
    # @websocket_test.manager.event('on_load')
    # def websocket_test():
    #     ...
    # @websocket_test.client.event('on_load')
    # def websocket_test():
    #     ...

    
    
class A_Local(Local_Entity_Base):
    Entity_Type = Entity_Types.A
    interface = AB_Interface

    def __init__(self, unique_id, db_url):
        super().__init__()
        self.unique_id = unique_id
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

    def Find_Entity_From_Req(self, request:Request):
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
            
        new_row = table.New_From_Request(request)
        self.session.add(new_row)
        self.session.commit()
        return new_row    

class A_Foreign(Foreign_Entity_Base, DB_Base):
    __tablename__ = Entity_Types.A.value + '_Entity'
    Entity_Type   = Entity_Types.A
    interface     = AB_Interface
    
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
        self.port = header.get('port', default = '----')
        self.host = header.get('host', default = '----')
        
    def matches_request(self,request:Request, headers:Request.headers):
        return all([headers.get('Role', default = '') == self.Entity_Type.value,
                    headers.get('UID',  default = '') == self.unique_id])

    def export_auth(self,)->tuple:
        return tuple()
    
class B_Local(A_Local):
    Entity_Type   = Entity_Types.B 

class B_Foreign(Foreign_Entity_Base, DB_Base):
    __tablename__ = Entity_Types.B.value + '_Entity'
    Entity_Type   = Entity_Types.B 
    interface     = AB_Interface
    
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
        self.port = header.get('port', default = '----')
        self.host = header.get('host', default = '----')
        
    def matches_request(self,request:Request, headers:Request.headers):
        return all([headers.get('Role', default = '') == self.Entity_Type.value,
                    headers.get('UID',  default = '') == self.unique_id])

    def export_auth(self,)->tuple:
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
    host = '127.00.0.1',
    port = '4001',
))
inst_a.session.commit()
app_a  = inst_a.attach_to_app(FastAPI())


db_url = 'sqlite:///database_B.db'
inst_b = B_Local('TestEntityB',db_url)
inst_b.session.merge(A_Foreign(
    unqiue_id= 'TestEntityA',
    host = '127.00.0.1',
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