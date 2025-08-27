import requests
import fastapi

from enum        import Enum,EnumType
from types       import FunctionType
from typing      import Self
from inspect     import isclass,signature as _sig
from functools   import partial,wraps
from contextvars import ContextVar

global PRIMARY_ENTITY
PRIMARY_ENTITY : 'Entity' = None

class _unset():...

class Mode(Enum):
    ''' Call types, used in routing '''
    GET      = 'GET'
    POST     = 'POST'
    PATCH    = 'PATCH'
    DELETE   = 'DELETE'

    INTERNAL = 'INTERNAL'
    # CLI      = 'CLI'

class _def_dict_list(dict):
    def __missing__(self,key):
        self[key] = inst = []
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
                 this_role       : EnumType       = None,
                 this_state      : EnumType       = None,
                 requester_role  : EnumType       = None,
                 requester_state : EnumType       = None,
                 _callback       : FunctionType   = None,         
                 ):
        def wrapper(func):
            inst =  cls(func, mode, this_role, this_state, requester_role, requester_state)
            if _callback:
                _callback(inst)
            return inst
        return wrapper
        
    # def __get__(self, inst, inst_cls):
    #     #May or may not work correctly when stored in a list?
    #     if inst is None: return self
    #     else: return partial(self,inst)

    def __call__(self, 
                 api_item    :'_Api_Item'  , 
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

class _Api_Item():
    ''' Should only be analagous interface for each method, instead of all '''

    def __init__(self,func,path,*args,**kwargs):
        self._func_base = func
        self._path      = path
        self._f_args    = args
        self._f_kwargs   = kwargs
        self._modes     = _def_dict_list()

    @classmethod
    def _wrapper(cls,path,*args,**kwargs):
        def wrapper(func):
            return cls(func,path,*args,**kwargs)
        return wrapper

    # def __get__(self,interface,inst_cls):
    #     assert issubclass(interface.__class__,(Interface,Entity))
    #     return partial(self,interface)
        #Might interfeer with keyed??

    def __call__(self, interface, this_entity=None, *args,**kwargs):
        ''' Direct call, instead of routed call '''
        return self._internal_handler(interface, *args, **kwargs)
        return self._call_interface(interface, Mode.INTERNAL, None, interface.Root_Entity, None, *args, **kwargs)

    def get_path(self,**kwargs)->str:
        ''' Return an optionally formatting string of the path w/ all components in entity/interface/...  chain'''
        # via self.
        raise NotImplementedError('TODO: CALLED GET PATH')


    def _register(self, interface:'Interface', router:fastapi.APIRouter)->None:
        for k,fl in self._modes.items():
            if k is Mode.INTERNAL: continue
            args, kwargs = self._api_route_args(fl[0].func,k,interface)
            router.add_route(*args,**kwargs)
            print('ADDING TO ROUTER:', args,kwargs)
            print([x for x in router.routes])


    def _api_route_args(self,func,method,interface:'Interface')->tuple[tuple,dict]:
        ''' Pass in the arguments of path and such '''
        wrapped = self._wrapped_for_router(func,method,interface)
        path    = self._path

        return (path, wrapped) + self._f_args, {'methods':[method.value]} | self._f_kwargs
    
    def _wrapped_for_router(self,func,mode,interface:'Interface'):
        ''' Produces the incoming command handler for a function of each mode. '''
        
        print('ORIGINAL FUNC SIGNATURE:',_sig(func))
        sig = _sig(func)
        # @wraps(func)
        def wrapped(request:fastapi.Request,*args,**kwargs):
            Ext_Entity = interface.Root_Entity._entity_pool.ensure_request_entity(request)
            print('INSIDE OF WRAPPED:', request, Ext_Entity, args,kwargs)
            return self._external_handler(interface, mode, request, interface.Root_Entity, Ext_Entity, *args, **kwargs)
        wrapped.__name__ = func.__name__
        # wrapped.__signature__ = sig.replace(parameters=list(sig.parameters.values())[2:].insert(0,fastapi.Request))
        wrapped.__signature__ = sig.replace(parameters=list(sig.parameters.values())[2:])
            #Spoof signature to that of wrapped_request + original
        print('SIGNATURE:',_sig(wrapped))
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
        self._modes[inst.mode].append(inst)
        if key:
            setattr(self,key,inst)

    @wraps(_Api_Item_Func._wrapper)
    def Get(self,key=None, *args,**kwargs):
        return _Api_Item_Func._wrapper(Mode.GET,*args,**kwargs, _callback = partial(self._attach,key=key))
    @wraps(_Api_Item_Func._wrapper)
    def Post(self,key=None, *args,**kwargs):
        return _Api_Item_Func._wrapper(Mode.POST,*args,**kwargs, _callback = partial(self._attach,key=key))
    @wraps(_Api_Item_Func._wrapper)
    def Patch(self,key=None, *args,**kwargs):
        return _Api_Item_Func._wrapper(Mode.PATCH,*args,**kwargs, _callback = partial(self._attach,key=key))
    @wraps(_Api_Item_Func._wrapper)
    def Patch(self,key=None, *args,**kwargs):
        return _Api_Item_Func._wrapper(Mode.DELETE,*args,**kwargs, _callback = partial(self._attach,key=key))
    @wraps(_Api_Item_Func._wrapper)
    def Internal_Primary(self,key=None, *args,**kwargs):
        return _Api_Item_Func._wrapper(Mode.INTERNAL,*args,**kwargs, _callback =  partial(self._attach,key=key))
    # @wraps(_Api_Item_Func._wrapper)
    # def Cli(self, *args,**kwargs):
    #     return _Api_Item_Func._wrapper(Mode.CLI,*args,**kwargs, _callback = self._attach)

Api_Item = _Api_Item._wrapper

class Connection():
    ''' Sends data with formatted data from PRIMARY_ENTITY in the header. 
    Could be usefulle to make aware of Root_Entity when attached to a non-default?? '''
    
    Root_Entity : 'Entity'

    def __init__(self,ip,port):
        ...

    @property
    def Primary_Entity(self):
        global PRIMARY_ENTITY
        return PRIMARY_ENTITY
    
    def get(self,path,*args,**kwargs):
        raise NotImplementedError('HAVE NOT IMPLIMENTED THIS FUNC YET: get    ',path, args, kwargs)
    def post(self,path,*args,**kwargs):
        raise NotImplementedError('HAVE NOT IMPLIMENTED THIS FUNC YET: post   ',path, args, kwargs)
    def patch(self,path,*args,**kwargs):
        raise NotImplementedError('HAVE NOT IMPLIMENTED THIS FUNC YET: patch  ',path, args, kwargs)
    def delete(self,path,*args,**kwargs):
        raise NotImplementedError('HAVE NOT IMPLIMENTED THIS FUNC YET: delete ',path, args, kwargs)

class Interface:
    Root_Entity : 'Entity'
    Interface_Subpath : str
    _router     :  fastapi.APIRouter

    def __init__(self,parent:Self|'Entity'):
        self.Root_Entity = parent.Root_Entity
        self._setup_interfaces()

    def _setup_interfaces(self):
        for k in dir(self):
            if isclass(v:=getattr(self,k)) and not k.startswith('_'):
                if issubclass(v,Interface):
                    setattr(self,k,v(self))

    def _iter_interfaces(self):
        for k in dir(self):
            if not isclass(v:=getattr(self,k)) and not k.startswith('_'):
                if issubclass(v.__class__,Interface):
                    yield v

    def _iter_apifuncs(self):
        for k in dir(self):
            v = getattr(self,k)
            print(k,v)
            if isinstance(v, _Api_Item):
                yield v
    
    def _register(self,router):
        self._router = self.make_router()
        for x in self._iter_apifuncs():
            x._register(self, self._router)
        for x in self._iter_interfaces():
            x._register(self._router)
        # self.Interface_Subpath,
        print('INTERFACE ROUTER ADDING:', self._router.routes)
        router.include_router(self._router, prefix = self.Interface_Subpath)
        print('HEAD ROUTES:', router.routes)

    def make_router(self):
        return fastapi.APIRouter()

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
        self.Is_Local     = True
        self.Root_Entity  = self
        self._setup_interfaces()
        self._entity_data = self._entity_data._init_in_parent_(self)

    def _setup_interfaces(self):
        for k in dir(self):
            if isclass(v:=getattr(self,k)) and not k.startswith('_'):
                if issubclass(v,Interface):
                    setattr(self,k,v(self))

    def _iter_interfaces(self):
        for k in dir(self):
            if not isclass(v:=getattr(self,k)) and not k.startswith('_'):
                if issubclass(v.__class__,Interface):
                    yield v
    @classmethod
    def As_Connection(cls,connection)->Self:
        #No entity-connection should be aware of it's entity_pool container.
        inst = cls()
        inst.connection = connection
        inst.conn_state = inst._entity_pool._default_con_state
        inst.Is_Local   = False
        inst.Start_App  = None
        return inst
    
    @classmethod
    def As_Connection_From_Request(cls,request:fastapi.Request,entity_data)->Self:
        ...
        # inst = cls.As_Connection(Connection(request.url,request.port) )
        # inst._entity_data = entity_data
    
    @classmethod
    def As_Undeclared_Connection(cls,entity_data):
        inst = cls()
        inst.connection   = None
        inst._entity_data = entity_data
        inst.conn_state   = inst._entity_pool._default_con_state
        inst.Is_Local     = False
        inst.Start_App    = None
        return inst

    def Setup_App(self,data=None):
        ''' App create & preperation (such as registeration)'''
        assert self.Is_Local        
        self._data = data
        self.Prepare_Self(data)
        self._router = self.Get_Router(data)
        for x in self._iter_interfaces():
            x._register(self._router)

        self._app    = self.Get_App(data,self._router)

        self._entity_pool = self._entity_pool(self)

        global PRIMARY_ENTITY
        PRIMARY_ENTITY = self

        return self._app

    def Prepare_Self(self,data):
        ...
    
    def Get_Router(self,data):
        router = fastapi.APIRouter()
        return router

    def Get_App(self, data, router:fastapi.APIRouter):
        app = fastapi.FastAPI()
        # app.add_api_route('/',router)
        app.include_router(router)
        return app
    

class Entity_Pool():
    ''' Contain a list of all connections & entities, 
    TODO: include timeout for undet and way to save/load connections+states for manager?
        - May just do manually depending on distance of use case 
    '''
    
    Primary_Entity : Entity
    Entities       : list[Entity]

    Int           : Enum         # Internal, Root_Entity.Role (As interfaces can be shared accross entities, this represents local)
    Ext           : Enum         # Enternal, Root_Entity.Role (As a connection)
    Conn_States   : Enum = set() # Connection State (Ext Only)
    Entity_States : Enum = set() # Entity     State (IE uninitialized, ect)

    entities          : list[Entity]   #All non-local
    _default_signed   : Entity
    _default_unsigned : Entity

    def __init_subclass__(cls):
        assert hasattr(cls,'Entities')
        for x in cls.Entities:
            x._entity_pool = cls

    def __init__(self, parent:Entity):
        self.Primary_Entity = parent

        assert not hasattr(self,'Int')
        assert not hasattr(self,'Ext')
        # self.Int = type('Int',(Enum,),{x.Entity_Role:x for x in self.Entities})
        # self.Ent = type('Ext',(Enum,),{x.Entity_Role:x for x in self.Entities if x._allow_external})
        self._Entities = {x.Entity_Role:x for x in self.Entities}
        self.Int = Enum('Int',self._Entities)
        self.Ext = Enum('Ext',self._Entities)


        self.Conn_States   = self._ensure_Enum('Conn_States'  ,getattr(self,'Conn_States'))
        self.Entity_States = self._ensure_Enum('Entity_States',getattr(self,'Entity_States'))

        self.entities = []

    def _interpret_Enum(self,desc:str)->EnumType:
        ''' Returns an enum's item from a desc w/a. Otherwise returns _unset '''

    def _ensure_Enum(self,name:str,existing:None|list|Enum):
        assert existing is not None
        if isclass(existing):
            return existing
        elif isinstance(existing,(tuple,set,list)):
            return Enum('Dyanic_enum',{x:x for x in existing})
            # return type('enum',(Enum,),{x:x for x in existing})
        else:
            raise Exception('')

    def ensure_request_entity(self,request):
        ''' Determine object type and default state based on request header
        Req_Header. -> Entity info -> Merge or New
           '''
        # a = getattr(self.Ext,request.header['role'],None)
        role = request.headers.get('role', default = None)
        if role is None:
            entity_type = self._default_unsigned
        else: 
            entity_type = self._Entities.get(role,default = self._default_signed)
        
        u_entity_data = entity_type._entity_data._init_foreign_(request)
        
        for e in self.Entities:
            if e._entity_data == u_entity_data:
                e._entity_data._intake_foreign_contact_(u_entity_data)
                return e

        if role is None:
            return entity_type.As_Undeclared_Connection(u_entity_data)

        return entity_type.As_Connection_From_Request(request,u_entity_data)

    def add_entity(self,entity):
        ''' force add an entity, TODO: tighten up entity pool logic '''
        self.entities.append(entity)

    def __getitem__(self,key):
        return self.entities[key]

class Entity_Data():
    Is_Local        : bool
    Entity_Role     : str
    Published_Attrs : list = tuple()  #List of all attributes published by the pimary entity, 

    #FUGLY, IK, Should probably make foreign data a derived/constructed instead of the same?
    @classmethod
    def _init_in_parent_(cls, parent: Entity):
        inst = cls()
        inst.Entity_Role = parent.Entity_Role
        inst.Root_Entity = parent
        inst.Is_Local    = parent.Is_Local
        return inst
    
    @classmethod
    def _init_foreign_(cls, request:fastapi.Request):
        return cls()

    def __init__(self):
        ...

    def _intake_foreign_contact_(self, foreing_data:Self):
        assert not self.Is_Local
        print('FOREIGN CONTACT INTAKE RUN')

    def _post_header_data_(self)->dict:
        print('HEADER DATA POST RUN')
    


if __name__ == '__main__':
    
    #EXAMPLE

    class Shared_Interface(Interface):
        Interface_Subpath = '/cmds'

        @Api_Item('/ping/{msg}',)
        def ping(self,entity, msg)->str:
            return f'suceeded {msg} from {entity.connection.ip}'

        @ping.Get(this_role = 'Ext', ) # this_state = 'States.Trusted') #Sender
        def _ping(self,entity, msg):
            return self.Root_Entity.connection.get(self.ping.get_path(), msg)
        
        @ping.Internal_Primary()
        def _ping(self,root_entity,msg):
            root_entity._entity_pool[0].cmds.ping(msg) 
            #if this object is the primary entity and the call is internal. 
        
    class common_entity_data(Entity_Data):
        ''' What to share in the header when communicating, Should be unique ID to object, requires mergeable info. 
        If a new connection the entity should become untrusted again '''

    class Undeclared(Entity):
        Entity_Role = 'Undeclared'
        _entity_data = common_entity_data

    class A(Entity):
        Entity_Role = 'A'
        cmds = Shared_Interface
        _entity_data = common_entity_data

    class B(Entity):
        Entity_Role = 'B'
        cmds = Shared_Interface
        _entity_data = common_entity_data

    class entity_pool(Entity_Pool):
        _default_signed   = Undeclared #Signed but incompatable 
        _default_unsigned = Undeclared 
        Entities = [A, B, Undeclared]

        class Conn_States(Enum):
            DEFAULT = 'DEFAULT'
            
        class Entity_States(Enum):
            DEFAULT = 'DEFAULT'

        _default_con_state = Conn_States.DEFAULT
        _default_ext_state = Entity_States.DEFAULT



    import argparse
    import sys
    import subprocess
    parser = argparse.ArgumentParser()
    parser.add_argument('-start_test',action='store_true',default = False,required=False)
    parser.add_argument('-inst',      type = str, required=False)
    parser.add_argument('-this_ip',   type = str, required=False)
    parser.add_argument('-this_port', type = str, required=False)
    parser.add_argument('-o_ip',      type = str, required=False)
    parser.add_argument('-o_port',    type = str, required=False)
    # parser.add_argument('-h','--help',    type = str, required=False)
    args, _u = parser.parse_known_args(sys.argv)
    print('GOT HERE')
    
    if args.start_test:
        a_data = {'name':'a', 'ip':'127.0.0.1', 'port':'4000'}
        b_data = {'name':'b', 'ip':'127.0.0.1', 'port':'4001'}

        cmd = f'python {__file__} -inst {a_data['name']} -this_host {a_data['ip']} -this_port {a_data['port']} -o_ip {b_data['ip']} -o_port {b_data['port']}'
        print(cmd)
        subprocess.run(cmd, shell=True)
        cmd = f'python {__file__} -inst {b_data['name']} -this_host {b_data['ip']} -this_port {b_data['port']} -o_ip {a_data['ip']} -o_port {a_data['port']}'
        subprocess.run(cmd, shell=True)

        # cmd = f'python -m uvicorn {__file__}:app --host {a_data['ip']} --port {a_data['port']} -inst {a_data['port']} -o_ip {b_data['ip']} -o_port {b_data['port']}'
        # subprocess.run(cmd, shell=True)
        # cmd = f'python -m uvicorn {__file__}:app --host {b_data['ip']} --port {b_data['port']} -inst {b_data['port']} -o_ip {a_data['ip']} -o_port {a_data['port']}'
        # subprocess.run(cmd, shell=True)

        #TODO: Add list, wait, timeout for test module for pass/fail based on exit codes
        sys.exit()

    match args.inst:
        case 'a':
            a = A()
            app = a.Setup_App()
            other_entity_cls = B
        case 'b':
            b = B()
            app = b.Setup_App()
            other_entity_cls = A
        case _:
            raise Exception


    import asyncio

    def test_connection():
        global PRIMARY_ENTITY
        print(PRIMARY_ENTITY._entity_pool[0].cmds.ping())
        
    async def run_tests():
        while True:
            asyncio.create_task(test_connection())
            await asyncio.sleep(3)

    # @app.on_event('startup')
    # async def app_startup():
    #     global PRIMARY_ENTITY
    #     PRIMARY_ENTITY._entity_pool.add_entity(other_entity_cls.As_Connection(Connection(args.o_ip, args.o_port)))
    #     # add connection from scratch, add to enttity and load directly into the entity pool instance.
    #     asyncio.create_task(run_tests())

    @app.get("/url-list")
    def get_all_urls():
        url_list = [{"path": route.path, "name": route.name} for route in app.routes]
        return url_list


    import uvicorn
    uvicorn.run(app, host = args.this_ip, port = args.this_port)

    # from fastapi.utils import repeat
    # from fastapi_utils.tasks import repeat_every

    # @app.on_event("startup")
    # @repeat_every(seconds=60 * 60)  # 1 hour
    # def remove_expired_tokens_task() -> None:
    #     with sessionmaker.context_session() as db:
    #         remove_expired_tokens(db=db)
    # import uvicorn
    # uvicorn.run(app,host="127.0.0.1", port=5000, log_level="info")

