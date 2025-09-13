from types     import FunctionType
from inspect   import isclass
from functools import partial
from typing    import Self
from enum      import Enum

from .Struct_Scheduled_Task import Scheduled_Task, Scheduled_Task_Pool
from datetime import datetime
EVENT_GUID_BIN = {}

class _Event_Types(Enum):
    PUB      = 'PUB' 
    SUB      = 'SUB' 
    BUFFER   = 'BUFFER' 
    READER   = 'READER' 
    SCHEDULE = 'SCHEDULE'

    META_SUB = 'META_SUB'       #Meaning Router Events that happen local only 


class Event_Item():
    ''' Wrapper classes instanced on each item. 
    Due to Order of operations, __get__ does not work unless it it's directly on the parent class 
    Considering using an Event_Item_Wrapper class to operate as an instance-buffer.
    '''

    func : FunctionType

    @classmethod
    def New(cls, router:'Event_Router', mode:_Event_Types, func, event_key='', **w_kwargs):
        new = type(f'Constructed_Event_Item:{mode.value}', (Event_Item,), w_kwargs)
        new.router_cls  = router
        new.mode        = mode
        new.event_key   = event_key
        new.func        = staticmethod(func)
        new.w_kwargs    = w_kwargs
        return new

    def __init__(self,router_inst):
        self.router = router_inst
        self.router.event_children[self.mode].append(self)
        # print('ATTACHED TO EVENT CHILDREN:', self.router, self.mode,self)
        
        if isclass(self.func):
            if issubclass(self.func,Event_Item): 
                self.func = self.func(router_inst)

    def __call__(self, container,*args,**kwargs):
        match self.mode:
            case _Event_Types.PUB:
                res = self.func(container,*args,**kwargs)
                self.router.publish(self,self.event_key, container, **self.w_kwargs)
                return res

            case _Event_Types.SUB:
                return self.func(container,*args,**kwargs)
            
            case _Event_Types.SCHEDULE:
                task = self.router.create_scheduled_task(self.func,container,*args,**kwargs)
                if self.auto_run:
                    self.router.attach_scheduled_task(task,interval=self.interval, start_delay=self.start_delay, scheduled_last_ran=self.scheduled_last_ran, uid=self.uid, guid=self.guid, max_iterations = self.max_iterations)
                return task

            case _:
                raise Exception(f'UNKNOWN MATCH: {self.mode}')

class _def_dict_list(dict):
    def __missing__(self,key):
        self[key] = inst = []
        return inst

class Event_Router():
    Constructed     = False
    
    router_parent   : Self|None
    router_children : list 

    Event_Children  : _def_dict_list  # Children on construction  add themselves to this dict[Enum|list]
    event_children  : _def_dict_list  # Children on instanciation add themselves to this dict[Enum|list]

    @classmethod
    def New(cls, filter = None, readout = False ,**extras):
        new = type(f'Constructed_Event_Router', (Event_Router,), {})
        new.Constructed     = True
        new.Readout         = readout
        new.Event_Children  = _def_dict_list()
        new.filter          = filter
        new.extras = extras
        return new

    @classmethod
    def Pub(cls,event_key,/, filter = None, local_only:bool=False): 
        return cls.create_factory_wrapper(_Event_Types.PUB, event_key, filter=filter, local_only=local_only)
    @classmethod
    def Sub(cls,event_key,/, filter = None, local_only:bool=False): 
        return cls.create_factory_wrapper(_Event_Types.SUB, event_key, filter=filter, local_only=local_only)
    @classmethod
    def Schedule(cls, /, event_key='', filter = None, local_only:bool=False, uid = None, guid = None, interval = None, start_delay = None, auto_run=False, attach_on_startup=False, scheduled_last_ran : FunctionType|int=None, scheduled_absolute=None,max_iterations=None ): 
        if auto_run: assert interval
        return cls.create_factory_wrapper(_Event_Types.SCHEDULE, event_key='', uid = uid, guid = guid, interval = interval, start_delay = start_delay, auto_run = auto_run, attach_on_startup=attach_on_startup, scheduled_absolute=scheduled_absolute, scheduled_last_ran = scheduled_last_ran, max_iterations=max_iterations )

    @classmethod
    def create_factory_wrapper(cls,mode,event_key,*args,**kwargs):
        assert cls.Constructed
        def wrapper(func):
            new = Event_Item.New(cls, mode, func,event_key, *args,**kwargs)
            cls.Event_Children[mode].append(new)
            return new
        return wrapper


    def pub(self,event_key,/, filter = None, local_only:bool=False): 
        return self.create_instance_wrapper(_Event_Types.PUB, event_key, filter=filter, local_only=local_only)
    
    def sub(self,event_key,/, filter = None, local_only:bool=False): 
        return self.create_instance_wrapper(_Event_Types.SUB, event_key, filter=filter, local_only=local_only)
    
    def schedule(self, /, event_key='', filter = None, local_only:bool=False, uid = None, guid = None, interval = None, start_delay = None, auto_run=False, attach_on_startup=False, scheduled_last_ran : FunctionType|int=None, scheduled_absolute=None,max_iterations=None ): 
        if auto_run: assert interval
        return self.create_instance_wrapper(_Event_Types.SCHEDULE, event_key='', uid = uid, guid = guid, interval = interval, start_delay = start_delay, auto_run = auto_run, attach_on_startup=attach_on_startup, scheduled_absolute=scheduled_absolute, scheduled_last_ran = scheduled_last_ran, max_iterations=max_iterations )

    def create_instance_wrapper(self,mode,event_key,*args,**kwargs):
        assert self.Constructed
        def wrapper(func):
            new = Event_Item.New(self, mode, func, event_key, *args, **kwargs)(self)
            self.event_children[mode].append(new)
            return new
        return wrapper
    #TODO: Test these instance based ones better!
    


    def __init__(self, container, parent=None):
        self._container      = container
        self.router_parent   = parent
        self.router_children = []
        self.event_children  = _def_dict_list()
        self.scheduled_task_pool = Scheduled_Task_Pool()
        self._format_container(container)

    def temp_attach_router_inst(self,router_inst):
        print('temp_attach_router_inst') 
        self.router_children.append(router_inst)
        return lambda : self.router_children.remove(router_inst); print ('REMOVED TEMP ROUTER : ', router_inst)
        

    def _format_container(self,container):
        ''' Ensure that all Event_Item children are instanciated '''
        for k in dir(container):
            if k.startswith('__'): continue
            v = getattr(container, k)
            # if v in self.Event_Children.any:
            if getattr(v,'router_cls', None) is self.__class__: 
                # print(v,v.__class__, id(getattr(v,'router_cls', None)), id(self.__class__))
                setattr(container,k,partial(v(self),container))
        self._format_readers()
        self._auto_register_schedule()
    
    def _auto_register_schedule(self):
        ...

    def _format_readers(self):
        for buffer in self.event_children[_Event_Types.BUFFER]:
            for reader in self.event_children[_Event_Types.READER]:
                if buffer.__class__ is reader.Buffer_Parent_Cls:
                    buffer.readers.append(reader)
                    reader.buffer = buffer
    
    def publish(self, event, event_key, container, /, is_local=True, filter=None, local_only=False, **kwargs):
        if self.Readout: print('PUB CALLED',event)
        if filter is not None:
            if filter(self._container,event_key,container): 
                return
        
        if self.router_parent and (not local_only):
            self.router_parent.publish(event,event_key,container,**kwargs)
            return

        self.call_subs(event, event_key, container, is_local=True, local_only=local_only, **kwargs)

    def call_subs(self, event, event_key, container, /, is_local:bool=False, local_only=False, **kwargs):
        if self.Readout: print('SUB CALLED',event,event_key,container,'THIS CONTAINER:',self._container, 'SELF CHILDREN:',self.router_children)
        for x in self.event_children[_Event_Types.SUB]:
            if x.event_key != event_key:
                continue
            if (not is_local) and x.local_only:
                continue
            if x.filter is not None:
                if not x.filter(self._container,event_key,container):
                    continue
            x(self._container, event, event_key, container, **kwargs)

        if (not local_only) or (is_local and local_only):
            for x in self.router_children:
                print(f'CALLING CHILD: {x}')
                # raise Exception('CALLING CHILDREN!')
                x.call_subs(event,event_key,container, **kwargs)
    
    def create_scheduled_task(self,func, *args, **kwargs):
        task =  Scheduled_Task(func, *args, **kwargs)
        # self.scheduled_task_pool._created.append(task)
        return task

    def attach_scheduled_task(self, task, interval:int, start_delay=0, uid=None, guid=None, scheduled_absolute=None, scheduled_last_ran=None, max_iterations = None):
        if guid:
            assert guid not in EVENT_GUID_BIN.keys()
            # if item:=EVENT_guid_BIN.get(guid,None):
            #     assert not item.is_running
        if callable(scheduled_last_ran):
            scheduled_last_ran = scheduled_last_ran()
            assert isinstance(scheduled_last_ran,datetime)
        elif isinstance(scheduled_last_ran,str):
            scheduled_last_ran = datetime.fromisoformat(scheduled_last_ran)
        elif isinstance(scheduled_last_ran,int):
            scheduled_last_ran = datetime.fromtimestamp(scheduled_last_ran)
        
        if scheduled_last_ran:
            #Resumption of a schedule if scheduled_last_ran is resolves
            start_delay = max(start_delay, (datetime.now() - scheduled_last_ran.timestamp() - interval))
        
        if not scheduled_absolute:
        #     raise Exception(self.scheduled_task_pool)
            return self.scheduled_task_pool.attach_and_run(task, interval=interval, start_delay=start_delay, UID=uid, max_iterations=max_iterations)
        else:
            raise NotImplementedError('TODO: Absolute scheduling that doesnt start after an intial delay.')
            return self.scheduled_task_pool.attach_and_run_absolute(task, UID=uid, date=scheduled_absolute, last_ran=last_ran)
            #Would like to fix so I can have set schedules that do *not* resolve at first optertunity in relation, but rather with absolute scheduling, cron-job style

    def container_removed(self):
        self.scheduled_task_pool.close_all('container_removed')