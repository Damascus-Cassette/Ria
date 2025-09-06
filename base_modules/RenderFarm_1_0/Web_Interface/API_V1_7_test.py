''' Example that starts up pool in memory and two apps for an ext command to run 
Full user case will have settings containers/methods on Local Entities that control the app startup & runtime settings
'''

from sqlalchemy     import (Column              ,
                            Boolean             ,
                            ForeignKey          ,
                            Integer             ,
                            String              ,
                            create_engine       ,
                            Table               )

from sqlalchemy.orm import (declarative_base    , 
                            relationship        , 
                            sessionmaker        , 
                            Mapped              , 
                            mapped_column       )


from .API_V1_7      import (Interface_Base      , 
                            Foreign_Entity_Base , 
                            Local_Entity_Base   ,
                            OL_IO               )

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

    def export_header(self, to_entity:Foreign_Entity_Base)->dict:
        return {'Role':self.Entity_Type.value}
    
class A_Foreign(Foreign_Entity_Base, DB_Base):
    __tablename__ = Entity_Types.A.value 
    Entity_Type   = Entity_Types.A

    def export_header(self, from_entity:Local_Entity_Base)->dict:
        return {}
    
    def intake_header(self, request, header):
        pass

    def matches_header(self,header):
        return header.get('Role', '') == self.Entity_Type.value

    def export_auth(self,)->tuple:
        return tuple()

    
    Interface = AB_Interface


class B_Local(Local_Entity_Base):
    Entity_Type = Entity_Types.B

    def export_header(self, to_entity:Foreign_Entity_Base)->dict:
        return {'Role':self.Entity_Type.value}

class B_Foreign(Foreign_Entity_Base, DB_Base):
    __tablename__ = Entity_Types.B.value 
    Entity_Type   = Entity_Types.B

    def export_header(self, from_entity:Local_Entity_Base)->dict:
        return {}
    
    def intake_header(self, request, header):
        pass

    def matches_header(self,header):
        return header.get('Role', '') == self.Entity_Type.value

    def export_auth(self,)->tuple:
        return tuple()
    
    Interface = AB_Interface


class Connection_Pool():
    ''' Dedup interface for entities '''
TODO
    def __init__():
        ...    

db_url = 'sqlite:///database.db'
engine  = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

DB_Base.metadata.create_all(engine)



