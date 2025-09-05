''' Application modes/contexts '''

from .Web_Interface.API_V1_6 import Entity,Entity_Data,Entity_Pool,Interface_Base,OL_Container
from ...models.struct_file_io import BaseModel
from .Entity_Settings    import Manager_Settings, Worker_Settings, Database_Settings

from enum import Enum

class Entity_Con_States(Enum):
    ''' States of entity-connection '''
    UNTRUSTED = 'UNTRUSTED'

class Entity_Ext_States(Enum):
    ''' State of entity-external '''
    DEFAULT   = 'DEFAULT'

class Entity_Int_States(Enum):
    ''' State of entity-interal '''
    DEFAULT   = 'DEFAULT'


class _DEFAULT_DATA(Entity_Data):
    Foreign_Match_keys = lambda *args: True
class _UNSIGNED(Entity):
    Entity_Role      = '_UNSIGNED'
    Entity_Data_Type = _DEFAULT_DATA
class _MALFORMED(Entity):
    Entity_Role      = '_MALFORMED'
    Entity_Data_Type = _DEFAULT_DATA

class Database_Data(Entity_Data):
    ...
class Database(Interface_Base): #Entity
    ''' Only an interface for the moment, 
    planning on distributed db app-entities eventually. (on worker, or as a caching db) 
        Will require comminication via manager to file being uploaded & where + movment of requested files.
        Out of scope for the mid-term
    '''
    ######## ENTITY STRUCTURE ########
    Entity_Role      = 'Database'
    Entity_Data_Type = Database_Data
    Settings_Handler = Database_Settings
        #Incoming dict settings applied as these objects

    ######## INTERFACE STRUCTURE ########
    Router_Subpath   = '/db'

    ######## Inst Data ########
    settings  : Database_Settings


class Manager_Data(Entity_Data):
    ...
class Manager(Entity):
    ''' App-Entity, handles files, job intake, task resolution, and endpoint exposure.
    Records signed unqiue connections' entity_data to db (w/ state and all that)
    Connections should have a timeout.
    To allow for a seperate service-db in the future, get-request-submit should have an endpoint to the db. (local or non-local) 
    '''
    ######## ENTITY STRUCTURE ########
    Entity_Role      = 'Manager'
    Entity_Data_Type = Manager_Data
    Settings_Handler = Manager_Settings
        #Incoming dict settings applied as these objects

    ######## SERVICES ########
    database         = Database
    
    ######## Inst Data ########
    settings  : Manager_Settings

class Worker_Data(Entity_Data):
    ...
class Worker(Entity):
    ''' App Entity, processes files/graphs, submits new tasks and cached results to manager (w/a) '''

    ######## ENTITY STRUCTURE ########
    Entity_Role = 'Worker'
    Entity_Data_Type = Worker_Data
    Settings_Handler = Worker_Settings
        #Incoming dict settings applied as these objects

    ######## Inst Data ########
    settings  : Worker_Settings

class Client_Data(Entity_Data):
    ...
class Client(Entity):
    ''' Non-App entity, Container for connection to manager(s) and ubiquitus contextual callbacks 
    Env stores settings & interacts with this datastructure, which is not kept cross-session.
    Calls endpoints on manager[ext] entities
    Should allow for webhooks for updates from manager (or reading rss feed?)
    Should allow both local and external proccessing of the graph.
    '''
    Entity_Role      = 'Client'
    Entity_Data_Type = Client_Data
    
    ######## SERVICES ########
    database         = Database


class _Entity_Pool(Entity_Pool):
    Default_Unsigned  = _UNSIGNED
    Default_Malformed = _MALFORMED
    
    Entity_Con_States = Entity_Con_States
    Entity_Ext_States = Entity_Ext_States
    Entity_Int_States = Entity_Int_States
    Default_Int_State = Entity_Int_States.DEFAULT  
    Default_Ext_State = Entity_Ext_States.DEFAULT  
    Default_Con_State = Entity_Con_States.UNTRUSTED
        #Consider on moving abovve block to each entity type.
            
    Entities = [
        _UNSIGNED     ,
        _MALFORMED    ,
        Worker        ,
        Manager       ,
        Client        ,
    ]

