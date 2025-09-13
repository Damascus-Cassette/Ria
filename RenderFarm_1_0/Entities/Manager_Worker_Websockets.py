
from typing import TypeAlias

from .Statics import Connection_States, Message_Topics ,Admin_Message_Actions ,Misc_Message_Actions ,VALUE_Message_Actions ,CRUD_Message_Actions,STATE_Message_Actions,Action_Message_Actions,ActionState_Message_Actions
from ..Web_Interface.Websocket_Pool import Manager_Websocket_Wrapper_Simul_Default, Websocket_Client,Websocket_Manager, Foreign_Entity_Base, Local_Entity_Base
from .EventSystem.Struct_Pub_Sub_v1_2 import Event_Router
from .Messsages import make_message, intake_message
from ..Web_Interface.API_V1_8 import Interface_Base, IO
import asyncio
Entity_Enums       : TypeAlias = None # Message_Topics.MANAGER_STATE|Message_Topics.WORKER_STATE|Message_Topics.CLIENT_STATE
Action_Enums       : TypeAlias = None # Message_Topics.JOB|Message_Topics.TASK|Message_Topics.GRAP|Message_Topics.CACHE
Action_State_Enums : TypeAlias = None # Message_Topics.JOB_STATE|Message_Topics.TASK_STATE|Message_Topics.GRAPH_STATE|Message_Topics.CACHE_STATE 


class message_websocket_common():
    ''' Doing this explicity is much better a filtered and broadcast pub-sub system for *every* message '''
    local_e    : Local_Entity_Base
    foreign_e  : Foreign_Entity_Base
    BufferType = list
    buffer     : list  

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.buffer = self.BufferType()

    def on_connection(self):
        self.local_e.commands.OBSERVE_Entity_State(Connection_States.CONNECTED)

    def produce_tasks(self,):
        return [
            self.recieve_json(),
            self.send_buffer (),
        ]

    async def recieve_json(self):
        msg = await self.websocket.recieve_json()
        topic, action, payload = intake_message(msg)

        match topic:
            case Message_Topics.ADMIN         : self.local_e.bidi_commands.REACT_Admin_Message (self, self.other_e, topic, action, payload)
            case Message_Topics.MISC          : self.local_e.bidi_commands.REACT_Misc_Message  (self, self.other_e, topic, action, payload)
            case Message_Topics.DATA          : self.local_e.bidi_commands.REACT_Data_Message  (self, self.other_e, topic, action, payload)
            case Message_Topics.CRUD          : self.local_e.bidi_commands.REACT_Crud_Message  (self, self.other_e, topic, action, payload)     

            case Message_Topics.JOB           : self.local_e.bidi_commands.REACT_Action_Message(self, self.other_e, topic, action, payload)        
            case Message_Topics.TASK          : self.local_e.bidi_commands.REACT_Action_Message(self, self.other_e, topic, action, payload)
            case Message_Topics.GRAPH         : self.local_e.bidi_commands.REACT_Action_Message(self, self.other_e, topic, action, payload)
            case Message_Topics.CACHE         : self.local_e.bidi_commands.REACT_Action_Message(self, self.other_e, topic, action, payload)

            case Message_Topics.MANAGER_STATE : self.local_e.bidi_commands.OBSERVE_Entity_State(self, self.other_e, topic, action, payload)
            case Message_Topics.WORKER_STATE  : self.local_e.bidi_commands.OBSERVE_Entity_State(self, self.other_e, topic, action, payload)
            case Message_Topics.CLIENT_STATE  : self.local_e.bidi_commands.OBSERVE_Entity_State(self, self.other_e, topic, action, payload)

            case Message_Topics.JOB_STATE     : self.local_e.bidi_commands.OBSERVE_Action_State(self, self.other_e, topic, action, payload)
            case Message_Topics.TASK_STATE    : self.local_e.bidi_commands.OBSERVE_Action_State(self, self.other_e, topic, action, payload)
            case Message_Topics.GRAPH_STATE   : self.local_e.bidi_commands.OBSERVE_Action_State(self, self.other_e, topic, action, payload)
            case Message_Topics.CACHE_STATE   : self.local_e.bidi_commands.OBSERVE_Action_State(self, self.other_e, topic, action, payload)
            
            case _: raise Exception('') 

    def on_close(self, error):
        if error:
            self.local_e.bidi_commands.OBSERVE_Entity_State(Connection_States.ERROR)
        else:
            self.local_e.bidi_commands.OBSERVE_Entity_State(Connection_States.CLOSED)

    def attach_message(self,*args,**kwargs):
        self.buffer.attach(make_message(*args,**kwargs))

class message_websocket_manager(message_websocket_common , Manager_Websocket_Wrapper_Simul_Default):...
class message_websocket_client(message_websocket_common  , Websocket_Client):...
    # Each 'Role' in the connection



class message_commands_common():
    Events = Event_Router.New()
    def __init__(self, local_entity):
        self.local_entity = local_entity
        self.events       = self.Events(self, local_entity.events)

    def REACT_Admin_Message (self, websocket, other_e:Foreign_Entity_Base, topic:Message_Topics.ADMIN , action:Admin_Message_Actions       , payload): ...
    def REACT_Misc_Message  (self, websocket, other_e:Foreign_Entity_Base, topic:Message_Topics.MISC  , action:Misc_Message_Actions        , payload): ...
    def REACT_Data_Message  (self, websocket, other_e:Foreign_Entity_Base, topic:Message_Topics.DATA  , action:VALUE_Message_Actions       , payload): ...
    def REACT_Crud_Message  (self, websocket, other_e:Foreign_Entity_Base, topic:Message_Topics.CRUD  , action:CRUD_Message_Actions        , payload): ...
    def OBSERVE_Entity_State(self, websocket, other_e:Foreign_Entity_Base, topic:Entity_Enums         , action:STATE_Message_Actions       , payload): ... 
    def REACT_Action_Message(self, websocket, other_e:Foreign_Entity_Base, topic:Action_Enums         , action:Action_Message_Actions      , payload): ...
    def OBSERVE_Action_State(self, websocket, other_e:Foreign_Entity_Base, topic:Action_State_Enums   , action:ActionState_Message_Actions , payload): ...
        #Websocket passed in to allow for immediate or bufferred events.

    def OBSERVE_Entity_State(self, other_e, value):
        assert issubclass(value, Connection_States)
        other_e.con_state = value

class Message_Commands_Manager(message_commands_common):...
class Message_Commands_Client(message_commands_common ):...
class Message_Commands_Worker(message_commands_common ):...



from fastapi import FastAPI
class message_interface_common(Interface_Base):
    router = FastAPI()
    
    ClientType  = message_websocket_client
    ManagerType = message_websocket_manager

    @IO.Websocket(router,'/bidi-data-stream')
    async def connection(self, this_e, other_e, websocket : Websocket_Manager)->None:
        app = self.ManagerType(this_e,other_e,websocket,id='bidi-data-stream')
        await app.accept()
        await app.run_handler()
            #Unfortunatly it looks like returning this function auto-closes the socket, which means I cannot return the app.
            #It is still accessable in the connection pool for it's lifespan however

    @connection.Client()
    async def _connection(self, this_e:Foreign_Entity_Base, other_e:Local_Entity_Base, path, headers)->message_websocket_client:
        fullpath = f'ws://{this_e.host}:{this_e.port}' + path
        
        app = self.ClientType(fullpath, headers=headers.items())
        
        try:
            app.connect()
            asyncio.create_task(app.run_forever())
            return app
        except Exception as e:
            print(f'Cound not connect! Reason: {e}')
            return None
        

class Message_Interface_Manager(message_interface_common):...
class Message_Interface_Client(message_interface_common):...
class Message_Interface_Worker(message_interface_common):...



