from enum   import Enum
from typing import Any
from inspect import isclass
from .EventSystem.Struct_Pub_Sub_v1_2 import Event_Router
from .Statics import Message_Topics

def make_message( id:str|None, topic:str|Message_Topics, action:str|Enum, payload:Any, router_inst:Event_Router=None, callback=None)->dict:
    ''' Create a message for a particular action, include an optional defined ID -> callback.
    Does this by temporarly attaching a sub to the router_inst that should pass in a cleanup function to the callback.
    This allows for temp and perm listeners on events.
    Bound_follow enum defined rules are also applied here
    '''

    if not isclass(topic)  : topic  = Message_Topics(topic)
    else: assert issubclass(topic, Message_Topics)
    if not isclass(action) : action = topic.bound_follow(action)
    else: assert issubclass(action, topic.bound_follow)
    if action.bound_follow : payload = action.bound_follow(payload)

    return [id, topic.value, action.value, payload]

    if callback:
        raise NotImplementedError('STILL WORKING ON IT :P')

    # @router_inst.publish()
    # async def callback():
    #     if is
    #     callback()
    #     ...

def intake_message(router_inst:Event_Router, data:list,)->list:
    ''' Convert message topic, action to types & return set callbacks? (maybe better via pub sub?) '''
    id, topic, action, *payload = data

    if not isclass(topic)  : topic   = Message_Topics(topic)
    if not isclass(action) : action  = topic.bound_follow(action)
    if action.bound_follow : payload[0] = action.bound_follow(payload[0])

    return id, topic, action, payload
