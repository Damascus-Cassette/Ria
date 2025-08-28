from .API_V1_6 import *


class Entity_Int_States(Enum):
    DEFAULT = 'DEFAULT_INT_STATE'
class Entity_Ext_States(Enum):
    DEFAULT = 'DEFAULT_EXT_STATE'
class Entity_Con_States(Enum):
    DEFAULT = 'DEFAULT_CON_STATE'

class _Entity_Data(Entity_Data):
    ''' Short circuits to declared roles assumed true & singleton of each
    NEVER DO IN PRODUCTION 
    #TODO: Also add middleware that adds additional security keys/IDs to incoming entities.
        # IE https_token, ip/port, jwt, decalred hardware specs  
        # Then consider measures for responce of change of each (IE new entity, change state, ect) 
    '''
    Foreign_Match_keys = lambda *args: True

class interface(Interface_Base):
    Router_Subpath = ''
    @OL_Container('/test')
    def test(self,this_entity,other_entity): 
        return f'TEST CALLED BY {other_entity}'
    
    # @test.Get_Deliver()
    @test.Get_Recieve()
    def _test(self,this_entity, other_entity) : 
        return f'{this_entity} {other_entity}'
        # raise NotImplementedError('TESTING')

class _UNSIGNED(Entity):
    Entity_Role = 'UNSIGNED'
    Entity_Data_Type = _Entity_Data

class _MALFORMED(Entity):
    Entity_Role = 'MALFORMED'
    Entity_Data_Type = _Entity_Data

class A(Entity):
    Entity_Role = 'A'
    Entity_Data_Type = _Entity_Data
    
    cmds = interface

class _Entity_Pool(Entity_Pool):  
    Default_Unsigned    = _UNSIGNED
    Default_Malformed   = _MALFORMED
    
    Entities = [A,]

    Entity_Int_States = Entity_Int_States
    Entity_Ext_States = Entity_Ext_States
    Entity_Con_States = Entity_Con_States

    Default_Int_State = Entity_Int_States.DEFAULT
    Default_Ext_State = Entity_Ext_States.DEFAULT
    Default_Con_State = Entity_Con_States.DEFAULT

SHARED_ENTITY_POOL = _Entity_Pool()

a = A._init_as_local_(SHARED_ENTITY_POOL)
app_a = a.Create_App()

a = A._init_as_local_(SHARED_ENTITY_POOL)
app_b = a.Create_App()

@app_a.get("/url-list")
@app_b.get("/url-list")
def get_all_urls():
    url_list = [{"path": route.path, "name": route.name} for route in app.routes]
    return url_list

# import uvicorn
# uvicorn.run(app, host = '127.0.0.1', port = '4000')

