''' Example that starts up pool in memory and two apps for an ext command to run 
Full user case will have settings containers/methods on Local Entities that control the app startup & runtime settings
'''

from sqlalchemy     import (Column              ,
                            Boolean             ,
                            ForeignKey          ,
                            Integer             ,
                            String              ,
                            create_engine       ,
                            Table               ,
                            Engine as EngineType,
                            )

from sqlalchemy.orm import (declarative_base    , 
                            relationship        , 
                            sessionmaker        , 
                            Mapped              , 
                            mapped_column       ,
                            Session as SessionType
                            )


from .API_V1_7      import (Interface_Base      , 
                            Foreign_Entity_Base , 
                            Local_Entity_Base   ,
                            OL_IO               )


from fastapi import Request
from enum import Enum

DB_Base = declarative_base()

class Entity_Types(Enum):
    A = 'A'
    B = 'B'
    UNDEC = 'UNDEC'

class UNDEC_Foreign(Foreign_Entity_Base):
    __tablename__ = Entity_Types.UNDEC.value 
    _interactive  = False
    Entity_Type   = Entity_Types.UNDEC

class AB_Interface(Interface_Base):
    
    @OL_IO('/test')
    def test(self,this_entity,other_entity):
        raise Exception('SHOULD NOT HIT THIS')

    @test.Get_Recieve()
    def _test(self,this_entity, other_entity) : 
        return f'{this_entity} {other_entity}'

    @test.Get_Send()
    def _test(self, this_entity, requesting_entity, raw_path, *args,**kwargs): 
        raise NotImplementedError('TODO')
        return this_entity.get(requesting_entity, raw_path, *args,**kwargs)


    @OL_IO('/list_entities')
    def list_entities():...

    @list_entities.Get_Recieve()
    def _list_entities(self, this_entity, other_entity):
        raise NotImplementedError('TODO')

    @list_entities.Get_Send()
    def _list_entities(self, this_entity, requesting_entity, raw_path, *args,**kwargs):
        raise NotImplementedError('TODO')
        return this_entity.get(requesting_entity, raw_path, *args,**kwargs)
        #  return self._Root_Entity.entity_pool.ext_pool._web_repr_()



class A_Local(Local_Entity_Base):
    Entity_Type = Entity_Types.A
    Interface = AB_Interface

    def __init__(self, unique_id, db_url):
        super().__init__()

        self.unique_id = unique_id

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
        return {'Role':self.Entity_Type.value, 'UID' : self.unique_id}

    def Find_Entity_From_Req(self, request:Request):
        ''' Ensure DB Connection, return foreign item '''
        for Table in [A_Foreign,B_Foreign]:
            for row in self.session.query(Table).execute().fetchall():
                if row.matches_request(request, request.headers):
                    row.intake_request(request, request.headers)
                    return row
        raise NotImplementedError('Should return a unique')
    

class A_Foreign(Foreign_Entity_Base, DB_Base):
    __tablename__ = Entity_Types.A.value + '_Entity'
    Entity_Type   = Entity_Types.A
    
    _Interface = AB_Interface

    def __init__(self,host,port):
        self.host = host
        self.port = port
        # self.id  = host + ':' +port

    id  = Column(Integer, primary_key=True)
    host = Column(String)
    port = Column(String)

    def export_header(self, from_entity:Local_Entity_Base)->dict:
        return {}
    
    def intake_request(self, request, header):
        pass

    def matches_request(self,request:Request, headers:Request.headers):
        return all(headers.get('Role', default = '') == self.Entity_Type.value,
                   headers.get('UID',  default = '') == self.unique_id)

    def export_auth(self,)->tuple:
        return tuple()


class B_Local(Local_Entity_Base):
    Entity_Type = Entity_Types.B
    Interface   = AB_Interface
    
    def __init__(self, unique_id, db_url):
        super().__init__()

        self.unique_id = unique_id
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
        return {'Role':self.Entity_Type.value, 'UID' : self.unique_id}

    def Find_Entity_From_Req(self, request:Request):
        ''' Ensure DB Connection, return foreign item '''
        for Table in [A_Foreign,B_Foreign]:
            for row in self.session.query(Table).execute().fetchall():
                if row.matches_request(request, request.headers):
                    row.intake_request(request, request.headers)
                    return row
        raise NotImplementedError('Should return a unique')

class B_Foreign(Foreign_Entity_Base, DB_Base):
    __tablename__ = Entity_Types.B.value + '_Entity'
    Entity_Type   = Entity_Types.B
    _Interface    = AB_Interface

    def __init__(self,host,port):
        self.host = host
        self.port = port
        # self.id  = host + ':' +port

    id  = Column(Integer, primary_key=True)
    host = Column(String)
    port = Column(String)

    def export_header(self, from_entity:Local_Entity_Base)->dict:
        return {}
    
    def intake_request(self, request, header):
        pass

    def matches_request(self,request:Request, headers:Request.headers):
        return all(headers.get('Role', default = '') == self.Entity_Type.value,
                   headers.get('UID',  default = '') == self.unique_id)

    def export_auth(self,)->tuple:
        return tuple()
    



from fastapi import FastAPI

db_url = 'sqlite:///database_A.db'
inst_a = A_Local('TestEntityA',db_url)
inst_a.session.add(B_Foreign(
    host = '127.00.0.1',
    port = '4001',
))
inst_a.session.commit()
app_a  = inst_a.attach_to_app(FastAPI())


db_url = 'sqlite:///database_B.db'
inst_b = B_Local('TestEntityB',db_url)
inst_b.session.add(A_Foreign(
    host = '127.00.0.1',
    port = '4000',
))
inst_b.session.commit()
app_b  = inst_b.attach_to_app(FastAPI())

#On app start, that one must be made active.




@app_a.get("/url-list")
def get_all_urls():
    url_list = [{"path": route.path, "name": route.name} for route in app_a.routes]
    return url_list
@app_b.get("/url-list")
def get_all_urls():
    url_list = [{"path": route.path, "name": route.name} for route in app_b.routes]
    return url_list

#python -m uvicorn Web_Interface.API_V1_7_test:app_a --port 4000 --reload
#python -m uvicorn Web_Interface.API_V1_7_test:app_b --port 4001 --reload