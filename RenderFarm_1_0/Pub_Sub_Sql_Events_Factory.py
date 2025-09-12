from .Struct_Pub_Sub_v1_2 import Event_Router
from sqlalchemy import event

def create_lister(table,event_key,router_inst):
    @event.listens_for(table,event_key)
    def event_listener(mapper,connection,target):
        router_inst.publish(None, event_key, target, is_local=True, mapper = mapper, connection = connection)
    return 

def set_listeners_on_table(table, router_inst, events:tuple[str] = ('after_insert', 'after_update', 'after_delete')):
    functions = []
    for event_key in events:
        functions.append(create_lister(table,event_key,router_inst))
            # router_inst.publish(event_key, None, target, _first_level=True, mapper = mapper, connection = connection)
            # router_inst.publish(None, event_key, target, local_only = True, mapper = mapper, connection = connection)
                #Should this be a local only one? 
    return functions

def set_listeners_on_tables(tables:list, root_router_inst:Event_Router, router_filter=None, events:tuple[str] = tuple(['after_insert', 'after_update', 'after_delete'])):
    ''' Quick n dirty way to add Router based Pub-Sub to all event tables, since the memory lifecycles on these database objects are indeterminate and thus cant be used for too much in current Event_Router methods '''
    for table in tables:
        router_inst = Event_Router.New(filter=router_filter, tablename=table.__tablename__)(None, parent = root_router_inst)
        set_listeners_on_table(table,router_inst,events=events)

