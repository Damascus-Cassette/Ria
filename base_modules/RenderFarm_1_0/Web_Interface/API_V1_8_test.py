
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
    
    @IO.Get(router1,'/path')
    def test(self, this_e, other_e, request,):
        return 'GET Test_Success'

    # @test.Send()
    # def _test(this_e, other_e, raw_path):
    #     return this_e.get(other_e, raw_path)

    @IO.Get(router1,'/path/{msg}')
    def test_1(self, this_e, other_e, request,msg):
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

    
# interface_example._register()