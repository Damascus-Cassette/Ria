
class event():
    creator  : Any
    do_with  : bool
    interval : ...


class interface_example():
    #Event is a post process
    
    Events = EventRouterType.Construct()

    # @Event.Auto_Register
    @Events.Pub('Event_Name') 
    def event_publisher(self):
        ...

    @Events.Pub('Event_Name', as_arg = True) 
    def event_publisher(self, publisher, ):
        ...
        publisher(wait = True, args, kwargs)
        ...

        # Wrapper version of:
        # self.root_entity.Event_Pool.Subscribe(Sub('Event_Name',event_publisher))
    
    # @Events.Auto_Register  
        #If this is done, Schedule must have intervol already set.
        #Otherwise you must call the function to set it up & track the event-holder yourself.
    # @Events.Auto_Register(time,this,that, args_kwargs = lambda self: (self.args,self.kwargs))  
    @Events.Schedule()
    def schedule_callback(self, task, *args,**kwargs):
        ''' Generator style schedule item '''

        ... #Run on opening

        while task.cont:
            ...   #Run every tick
            yield #wait till next tick.
        
        ... #Run on Closing

        #Timed event publisher, Sync or Async
        # On closing, timer should be removed from manager.
        
        #Router should take care of deletion

    @Events.Sub('Event_Name', Direct_Local=True)   #Masking to be direct local, always hit first. May or may not be async allowed with local  forced threaded.
    async def event_subscriber(self,event, ):
        self.root_entity.Event_Pool.Publish(BaseEventType('Event_Name',))

    @Events.Sub('Event_Name')
    @Events.Buffer()
    def event_buffer(self, buffer, event, x):
        #On event publishing, attach or not atrach to buffer.
        buffer.attach(x)

    @Events.Sub('Other_Event')
    @event_buffer.Reader
    def event_buffer_reader(self,buffer):
        #On event subcription trigger (Timed or otherwise), execution and optionally clear buffer.
        for x in buffer:
            x.do_somethiong()
        buffer.clear()
        


# The primary difference between hooks and pub-sub is that this should be async and system wide instead of per-instance, and does not allow wrapping/timing. All happen sync or async.
