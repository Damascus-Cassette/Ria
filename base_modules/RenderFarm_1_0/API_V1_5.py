import requests
import fastapi

from enum        import Enum,EnumType
from types       import FunctionType
from typing      import Self
from inspect     import isclass,signature as _sig
from functools   import partial,wraps
from contextvars import ContextVar

global PRIMARY_ENTITY
PRIMARY_ENTITY = None

class _unset():...

class Mode(Enum):
    ''' Call types, used in routing '''
    GET      = 'GET'
    POST     = 'POST'
    PATCH    = 'PATCH'
    DELETE   = 'DELETE'

    INTERNAL = 'INTERNAL'
    # CLI      = 'CLI'

class _def_dict_list():
    def __missing__(self,key):
        self[key] = inst = key
        return inst

class _Api_Item_Func():
    def __init__(self,
                 func            : FunctionType   ,
                 mode            : Mode           ,
                 this_role       : EnumType       , #Entity's role & Position, IE Int.Manager (Get Call) vs Ext.Manager (Make Call), Default Int
                 this_state      : EnumType       , #IE State.Untrusted vs State.Trusted, Typically None when Int unless special self states are important.
                 requester_role  : EnumType       , #Requester's role & position, IE Ext.Worker, Default Ext.  Req to be in Ext or Mode.INTERNAL/CLI
                 requester_state : EnumType       , #Required if Ext.
                 ):
        self.mode            = mode
        self.func            = func
        self.this_role       = this_role
        self.this_state      = this_state
        self.requester_role  = requester_role
        self.requester_state = requester_state
    
    @classmethod
    def _wrapper(cls,
                 mode            : Mode           ,
                 this_role       : EnumType       ,
                 this_state      : EnumType       ,
                 requester_role  : EnumType       ,
                 requester_state : EnumType       ,
                 __callback      : FunctionType   = None,         
                 ):
        def wrapper(func):
            inst =  cls(func, mode, this_role, this_state, requester_role, requester_state)
            if __callback:
                __callback(inst)
            return inst
        return wrapper
        
    def __get__(self, inst, inst_cls):
        #May or may not work correctly when stored in a list?
        if inst is None: return self
        else: return partial(self,inst)

    def __call__(self, 
                 api_item    :'Api_Item'  , 
                 interface   :'Interface' , 
                 this_entity :'Entity'    , 
                 *args, **kwargs          ,):
        ''' Direct call, regulardless of matching args '''
        return self.func(*args,**kwargs)
    
    def match(self,*args,**kwargs):
        ... #self.mode can be Mode.INTERNAL, which changes IO?
        ... #TODO: Filter based on context. Objects, Ie this.parent's.state
        # return self.filter(*args,**kwargs)
    
    def match_internal():
        ...
    def match_external():
        ...

class Api_Item():
    ''' Should only be analagous interface for each method, instead of all '''

    def __init__(self,func,path,*args,**kwargs):
        self._func_base = func
        self._path      = path
        self._f_args    = args
        self._f_kargs   = kwargs
        self._modes     = _def_dict_list()

    def __get__(self,interface,inst_cls):
        assert issubclass(interface.__class__,(Interface,Entity))
        return partial(self,interface)
    
    def __call__(self, interface, this_entity=None, *args,**kwargs):
        ''' Direct call, instead of routed call '''
        return self._internal_handler(interface, *args, **kwargs)
        return self._call_interface(interface, Mode.INTERNAL, None, interface.Root_Entity, None, *args, **kwargs)

    def _register(self, interface:'Interface', router:fastapi.APIRouter)->None:
        for k,fl in self._modes.items():
            args, kwargs = self._api_route_args(fl[0],k,interface)
            router.add_api_route(*args,**kwargs)

    def _api_route_args(self,func,method,interface:'Interface')->tuple[tuple,dict]:
        ''' Pass in the arguments of path and such '''
        wrapped = self._wrapped_for_router(func,interface)
        path    = self._path

        return (path, wrapped) + self._fapi_args, {'methods':[method]} | self._fapi_kwargs
    
    def _wrapped_for_router(self,func,mode,interface:'Interface'):
        ''' Produces the incoming command handler for a function of each mode. '''
        
        sig = _sig(func)
        def wrapped(request:fastapi.Request,*args,**kwargs):
            Ext_Entity = interface.Root_Entity._entity_pool.ensure_request_entity(request)
            return self._call_interface(interface, mode, request, interface.Root_Entity, Ext_Entity, *args, **kwargs)

        wrapped.__signature__ = sig.replace(parameters=list(sig.parameters.values())[2:].insert(0,fastapi.Request))
            #Spoof signature to that of wrapped_request + original
        return wrapped


    ######## HANDLER METHODS ######## 

    def _internal_handler(self,interface,*args,**kwargs):
        ''' Could be 
        - Ext calling self
        - primary calling primary indirect
        - prgm    calling primary indirect
        '''
        Root_Entity = interface.Root_Entity
        for r_func in self._modes[Mode.INTERNAL]:
            r_func : _Api_Item_Func
            if r_func.match(this_role = interface.Root_Entity):
                return r_func(interface,*args,**kwargs) 
        return self._func_base(interface,None,*args,**kwargs)

    def _external_handler(self, interface, mode:Mode, request, Root_Entity, Ext_Entity, *args,**kwargs):
        for r_func in self._modes[mode]:
            r_func : _Api_Item_Func
            if r_func.match(request,Root_Entity,Ext_Entity):
                return r_func(interface,Ext_Entity,request,*args,**kwargs) 
        return self._func_base(interface,Ext_Entity,*args,**kwargs)


    ######## WRAPPER METHODS ######## 

    def _attach(self, inst:_Api_Item_Func,key=None):
        self._modes[inst.mode].append(self)
        if key:
            setattr(self,key,inst)

    @wraps(_Api_Item_Func._wrapper)
    def Get(self,key=None, *args,**kwargs):
        return _Api_Item_Func._wrapper(Mode.GET,*args,**kwargs, __callback = partial(self._attach,key=key))
    @wraps(_Api_Item_Func._wrapper)
    def Post(self,key=None, *args,**kwargs):
        return _Api_Item_Func._wrapper(Mode.POST,*args,**kwargs, __callback = partial(self._attach,key=key))
    @wraps(_Api_Item_Func._wrapper)
    def Patch(self,key=None, *args,**kwargs):
        return _Api_Item_Func._wrapper(Mode.PATCH,*args,**kwargs, __callback = partial(self._attach,key=key))
    @wraps(_Api_Item_Func._wrapper)
    def Patch(self,key=None, *args,**kwargs):
        return _Api_Item_Func._wrapper(Mode.DELETE,*args,**kwargs, __callback = partial(self._attach,key=key))
    # @wraps(_Api_Item_Func._wrapper)
    # def Internal(self, *args,**kwargs):
    #     return _Api_Item_Func._wrapper(Mode.INTERNAL,*args,**kwargs, __callback = self._attach)
    # @wraps(_Api_Item_Func._wrapper)
    # def Cli(self, *args,**kwargs):
    #     return _Api_Item_Func._wrapper(Mode.CLI,*args,**kwargs, __callback = self._attach)
    
class Connection():
    ''' Sends data with formatted data from PRIMARY_ENTITY in the header '''
    
    Root_Entity : 'Entity'

    def __init__(self,):
        ...

    @property
    def Primary_Entity(self):
        global PRIMARY_ENTITY
        return PRIMARY_ENTITY
    
    def get():
        ...
    def post():
        ...
    def patch():
        ...
    def delete():
        ...

class Interface:
    Root_Entity : 'Entity'
    
    def __init__(self,parent:Self|'Entity'):
        self.Root_Entity = parent.Root_Entity
        self._setup_interfaces()

    def _setup_interfaces(self):
        for k in dir(self):
            if isclass(v:=getattr(self,k)):
                if issubclass(v,Interface):
                    setattr(k,v(self))

class Entity:
    _allow_external : bool = True

    Entity_Role  : str
    Root_Entity  : Self

    Is_Local     : bool 
    entity_state : EnumType

    connection   : Connection
    conn_state   : EnumType     #Item of Enum factory cls?

    _entity_pool : 'Entity_Pool'
    _entity_data : 'Entity_Data'
    _app         : fastapi.applications.AppType
    _router      : fastapi.APIRouter

    def __init__(self):
        ''' Setup the interfaces '''
        self.Root_Entity  = self
        self._setup_interfaces()
        self._entity_pool = self._entity_pool(self)
        self._entity_data = self._entity_data(self)

    def _setup_interfaces(self):
        for k in dir(self):
            if isclass(v:=getattr(self,k)):
                if issubclass(v,Interface):
                    setattr(k,v(self))

    @classmethod
    def As_Connection(cls,connection)->Self:
        #No entity-connection should be aware of it's entity_pool container.
        inst = cls()
        inst.connection = connection
        inst.conn_state = inst._entity_pool._default_con_state
        inst.Is_Local   = False
        inst.Start_App  = None
        return inst

    def Start_As_App(self,port,data):
        ''' Data to startup the App, such as port'''
        assert self.Is_Local        
        self._data = data
        self.Prepare_Self(data)
        self._router = self.Get_Router()
        self._app    = self.Get_App()
        self.Start_App(self._app, self._router)

        global PRIMARY_ENTITY
        PRIMARY_ENTITY = Self

    def Prepare_Self(self,data):
        ...
    
    def Get_Router(self,data):
        ...
    
    def Get_App(self,data):
        ...
    
    def Start_App(self, app, router:fastapi.APIRouter):
        ...

class Entity_Pool():
    ''' Contain a list of all connections & entities, 
    TODO: include timeout for undet and way to save/load connections+states for manager?
        - May just do manually depending on distance of use case 
    '''
    
    Primary_Entity : Entity
    Entities       : list

    Int           : Enum         # Internal, Root_Entity.Role (As interfaces can be shared accross entities, this represents local)
    Ext           : Enum         # Enternal, Root_Entity.Role (As a connection)
    Conn_States   : Enum = set() # Connection State (Ext Only)
    Entity_States : Enum = set() # Entity     State (IE uninitialized, ect)

    entities      : list[Entity]   #All non-local

    def __init__(self, parent:Entity):
        self.Primary_Entity = parent

        self.Int = type('Int',(Enum,),{x.Entity_Role:x for x in self.Entities})
        self.Ent = type('Ext',(Enum,),{x.Entity_Role:x for x in self.Entities if x._allow_external})
        
        self.Conn_States   = self._ensure_Enum(getattr(self,'Conn_States'))
        self.Entity_States = self._ensure_Enum(getattr(self,'Entity_States'))

        self.entities = []

    def _interpret_Enum(self,desc:str)->EnumType:
        ''' Returns an enum's item from a desc w/a. Otherwise returns _unset '''

    def _ensure_Enum(self,existing:None|list|Enum):
        assert existing is not None
        if isclass(existing):
            return existing
        elif isinstance(existing,(tuple,set,list)):
            return type('enum',(Enum,),{x:x for x in existing})
        else:
            raise Exception('')

    def ensure_request_entity(self,request):
        ''' Determine object type and default state based on request header
        Req_Header. -> Entity info -> Merge or New
           '''
        a = getattr(self.Ext,request.header['role'],None)
        ???
        _intake_header_data_


class Entity_Data():
    Is_Local        : bool
    Entity_Role     : str
    Published_Attrs : list = tuple()  #List of all attributes published by the pimary entity, 

    def __init__(self, parent:Entity):
        self.Entity_Role = parent.Entity_Role
        self.Root_Entity = parent
        self.Is_Local    = parent.Is_Local

    @classmethod
    def _init_foreign_(cls):
        ...

    def _post_header_data_(self)->dict:        
        ...

    def _intake_header_data_(self,header_data):
        assert not self.Is_Local
        # This can include changing parent entity_state, BUT NEVER connection_state
        ...
    


if __name__ == '__main__':
    
    #EXAMPLE

    class Shared_Interface(Interface):
        
        @Api_Item('ping')
        def ping(self,*args,**kwargs):
            return 404

        @ping.Get(this_role = 'Ext.A', this_state = 'States.Trusted') #Sender
        def _ping(self,arg):
            return self.Root_Entity.connection.get(self.ping.get_path(), arg)
        
    class common_entity_data(Entity_Data):
        ''' What to share in the header when communicating, Should be unique ID '''

    class A(Entity):
        Entity_Role = 'A'
        cmds = Shared_Interface
        _entity_data = common_entity_data

    class B(Entity):
        Entity_Role = 'B'
        cmds = Shared_Interface
        _entity_data = common_entity_data

    class entity_pool(Entity_Pool):
        Entities = [A,B]

    
    a = A().Start_As_App('localhost', '3000')
