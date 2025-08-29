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
        raise Exception('SHOULD NOT HIT THIS')
    
    @test.Get_Endpoint()
    def _test(self,this_entity, other_entity) : 
        return f'{this_entity} {other_entity}'

    @test.Get_Send()
    def _test(self, this_entity:'Entity', requesting_entity:'Entity', raw_path, *args,**kwargs): 
        return this_entity.entity_data.Connection.get(requesting_entity, raw_path, *args,**kwargs)


    @OL_Container('/list_entities')
    def list_entities():...

    @list_entities.Get_Endpoint()
    def _list_entities(self, this_entity, other_entity):
        return self._Root_Entity.entity_pool.ext_pool._web_repr_()
    
    @OL_Container('/test_peers')
    def test_peers(self, this_entity, other_entity):...


    @test_peers.Get_Endpoint() #.default_get() which should return original class and add item to list?
    def _test_peers(self, this_entity, other_entity):
        data = {}
        for k,e in self._Root_Entity.entity_pool.ext_pool._each_subitem_():                
            data[k] = ls = []
            if hasattr(e,'cmds'):
                ls.append( e.cmds.test.Send_Get(this_entity) )
        return data


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

class B(Entity):
    Entity_Role = 'B'
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


app_a_entity_pool = _Entity_Pool()
a = A._init_as_local_(app_a_entity_pool)
app_a = a.Create_App()
a.entity_pool.add_entity(B._init_from_connection_(app_a_entity_pool,host = '127.0.0.1', port = '4001'))

app_b_entity_pool = _Entity_Pool()
b = B._init_as_local_(app_b_entity_pool)
app_b = b.Create_App()
b.entity_pool.add_entity(A._init_from_connection_(app_b_entity_pool,host = '127.0.0.1', port = '4000'))


# def test_connection():
#     global PRIMARY_ENTITY
#     interface = PRIMARY_ENTITY._entity_pool[0].cmds 
#     print(interface.ping(interface, 'TestMessage'))
#     
# async def run_tests():
#     while True:
#         asyncio.create_task(test_connection())
#         await asyncio.sleep(3)
#
# @app_b.on_event('startup')
# async def app_startup():
#     global PRIMARY_ENTITY
#     SHARED_ENTITY_POOL.add_entity()
#     asyncio.create_task(run_tests())

@app_a.get("/url-list")
@app_b.get("/url-list")
def get_all_urls():
    url_list = [{"path": route.path, "name": route.name} for route in app.routes]
    return url_list

# import uvicorn
# uvicorn.run(app, host = '127.0.0.1', port = '4000')

#cd base_modules/RenderFarm_1_0  
#python -m uvicorn Web_Interface.API_V1_6_test:app_a --port 4000 --reload
#python -m uvicorn Web_Interface.API_V1_6_test:app_b --port 4001 --reload
