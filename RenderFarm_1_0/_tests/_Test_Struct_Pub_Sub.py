from ..Struct_Pub_Sub_v1_1 import Event_Router

from contextvars import ContextVar

test_1 = ContextVar('test_1', default = False)

# class my_meta_class():
#     Events = Event_Router.New()
    
#     def test_sub


class myclass():
    Events = Event_Router.New()

    def __init__(self):
        self.Events = self.Events(self)
    
    @Events.Pub('Event', local_only = True)
    def test_pub(self):
        print(self)
        
    @Events.Sub('Event')
    def test_sub(self, event, event_key, events_container):
        test_1.set(True)
        print('EVENT SUB CALLED ')

def test_myclass():
    inst = myclass()
    inst.test_pub()
    assert test_1.get()