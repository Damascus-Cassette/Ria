
import fastapi
import inspect
from functools import wraps, partial
from types     import FunctionType
from inspect   import isclass
from enum      import Enum

class Int(Enum):
    ''' If a call comes from an internal interface '''
    A = 'A' 
    B = 'B' 
    UNDECLARED  = 'UNDECLARED'
    
class Ext(Enum):
    ''' If a call comes from an external/connection interface '''
    A = 'A' 
    B = 'B' 
    UNDECLARED  = 'UNDECLARED'
    
class Role(Enum):
    ''' Implicitly External '''
    A = 'A'
    B = 'B'
    
class State(Enum):
    ''' External Connection State'''
    TRUSTED   = 'TRUSTED'
    UNTRUSTED = 'UNTRUSTED'

class CALLS(Enum):
    ''' Call types, used in routing '''
    GET      = 'GET'
    POST     = 'POST'
    PATCH    = 'PATCH'
    DELETE   = 'DELETE'

    INTERNAL = 'INTERNAL'
    CLI      = 'CLI'


class Connection():
    ''' Connection handling object, created with each incoming/outgoing interface.
    handles outgoing calls, entity handles incoming 
    Will optimize incoming connections later to only be trusted '''
    def __init__(self, ip, port, key=None, password=None):
        ...

    entity : 'Entity_Interface'

    def get(self,path,):
        ...
    def post(self,path,):
        ...
    def patch(self,path,):
        ...
    def delete(self,path,):
        ...

    def incoming():
        ...

from typing import Self
class Entity_Interface():
    ''' An entity interface that can be started in either a local or connection mode. Asc with a role'''
    is_local   : bool       = True
    connection : Connection = None
    con_state  : State     = State.UNTRUSTED
    connection_handler : 'Ext_Interface_Handlder'
    role         : Role
    role_mapping : dict
    
    @classmethod
    def as_connection(cls,connection:Connection)->Self:
        new = cls.__new__(cls)
        new.connection = connection
        new.con_state  = State.UNTRUSTED
        return new
    
    def __init_subclass__(cls):
        if di:=getattr(cls,'role_mapping',None):
            di[cls.role.value] = cls

    def _incoming_request(self):
        ''' Request that was parsed to be for this object as a connection '''
        assert not self.is_local
        assert self.connection
        ...


    def _subinterfaces_uninit(self):
        for k in dir(self):
            v = getattr(self,k)
            if not isclass(v):
                continue
            if issubclass(v,SubInterface):
                yield k,v

    def _subinterfaces(self):
        for k in dir(self):
            v = getattr(self,k)
            if isinstance(v,SubInterface):
                yield k,v

    def __new__(cls):
        self = super().__new__(cls) 
        ''' Place Object's Sub IO here '''
        for k,v in self._subinterfaces_uninit():
            setattr(self,k,v(self))
        return self

    def __init__(self):
        self.is_local = True
        self.connection_handler = Ext_Interface_Handlder(self)
        self.router             = self._make_router()
        for k,v in self._subinterfaces():
            v._register(self.router)
    
    def _make_router(self):
        return fastapi.APIRouter()


class SubInterface():
    ''' In short these interfaces should know all routed functions & their interfaces
    Also 
    '''
    _router      : fastapi.APIRouter | None 
    _path        : str


    def __init__(self,parent:Entity_Interface):
        self.parent = parent


    def _api_items(self):
        for k in dir(self):
            v = getattr(self,k)
            if isinstance(v,_api_item):
                yield k,v

    def _register(self,router:fastapi.APIRouter):
        self._router = self.make_router()
        for k,v in self._api_items():
            v._register(parent = self, router = router)
        router.add_route(self._path,self._router)

    def make_router(self,):
        return fastapi.APIRouter()


class Entity_Connection_Handler():
    ''' Singleton that handles all connections '''
    
    entites = []

    def  entity_rep_ensure(req)->Entity_Interface:
        ''' Takes a connection, returns the relevent entity and creates as required '''
        ...
    


class _routed_func():
    def __init__(self,
                 mode:CALLS      , 
                 func            , 
                 this_role       ,
                 this            ,
                 requester       ,
                 requester_state ,
                 ):
        self.mode            = mode
        self.func            = func
        self.this_role       = this_role
        self.this            = this
        self.requester       = requester
        self.requester_state = requester_state
        
    def __get__(self,inst,inst_cls):
        if inst is None: return self.__class__
        else:            return partial(self,inst)

    def __call__(self, parent, *args, **kwargs):
        ''' Direct call, regulardless of matching args '''
        return self.func(*args,**kwargs)
    
    def match(self,*args,**kwargs):
        ... #TODO: Filter based on context. Objects, Ie this.parent's.state
        # return self.filter(*args,**kwargs)


class _api_item():
    ''' API Function wrapper, registers functions to an API router object on call. 
    Enteres and exists context declareing role & context stuff as inline as possible
    Allows sub-functions that route based on context, otherwise falls back to first wrappped function.
    '''
    _routes = list[_routed_func]
    _path        : str
    _fapi_args   : tuple
    _fapi_kwargs : dict
    _func_base   : FunctionType

    def __init__(self,func, path, *args,**kwargs)->Self:
        self._func_base   = func
        self._path        = path
        self._fapi_args   = args
        self._fapi_kwargs = kwargs
        self._routes      = []
        self._methods     = []

    @classmethod
    def _init_wrapper(cls,path,*args,**kwargs):
        def wrapper(func):
            return cls(func,path,*args,**kwargs)

        return wrapper
    
    def __get__(self,inst,inst_cls):
        return partial(self,inst)

    def __call__(self, parent, *args,**kwargs):
        self._call_interface(parent, None, *args,**kwargs)

    def _register(self, parent:SubInterface, router:fastapi.APIRouter)->None:
        args, kwargs = self._api_route_arg(parent)
        router.add_api_route(*args,**kwargs)

    def _api_route_arg(self,parent:SubInterface)->tuple[tuple,dict]:
        ''' Pass in the arguments of path and such '''
        wrapped = self._produce_ext_handler(parent)
        path    = self._path

        return (path, wrapped) + self._fapi_args, {'methods':self._methods} | self._fapi_kwargs
    
    def _produce_ext_handler(self,parent:SubInterface):
        ''' Produces the incoming connection (ext->local) handler for a function '''
        #TODO: HAVE CONNECTION->ENTITY HANLDER INSERTED HERE
        
        sig = inspect.signature(self._func_base)
        
        def wrapped(request:fastapi.Request,*args,**kwargs):
            return self._call_interface(parent,request,*args,**kwargs)
        
        wrapped.__signature__ = sig.replace(parameters=list(sig.parameters.values())[2:].insert(0,fastapi.Request))        
        return wrapped


    def _wrapper(self, 
            mode            :CALLS               , 
            key             :str          = None , #Allows bypassing of wrapper in calling, for local calls and debugging
            this_role       :Role         = None , 
            this            :Int|Ext      = None , 
            requester       :Int|Ext|Role = None , 
            requester_state :State        = None ,
            ):
        ''' Add an item to the wrapper with above arguments '''
        def wrapper(func):
            if isinstance(func,_routed_func):
                func = func.func
            inst = _routed_func(
                        mode   = mode, 
                        func   = func,
                        this_role       = this_role, 
                        this            = this, 
                        requester       = requester, 
                        requester_state = requester_state,
                        )
            self._routes.append(inst)
            if key:
                setattr(self,key,inst)
            return inst
        return wrapper

    @wraps(_wrapper)    
    def Get(self,*args,**kwargs): 
        if CALLS.GET.value not in self._methods: 
            self._methods.append(CALLS.GET.value)
        return self._wrapper(CALLS.GET,*args,**kwargs)
    @wraps(_wrapper)    
    def Post(self,*args,**kwargs): 
        if CALLS.POST.value not in self._methods: 
            self._methods.append(CALLS.POST.value)
        return self._wrapper(CALLS.POST,*args,**kwargs)
    @wraps(_wrapper)    
    def Patch(self,*args,**kwargs): 
        if CALLS.PATCH.value not in self._methods: 
            self._methods.append(CALLS.PATCH.value)
        return self._wrapper(CALLS.PATCH,*args,**kwargs)
    @wraps(_wrapper)    
    def Delete(self,*args,**kwargs): 
        if CALLS.DELETE.value not in self._methods: 
            self._methods.append(CALLS.DELETE.value)
        return self._wrapper(CALLS.DELETE,*args,**kwargs)

    def _get_route_path(self):
        ''' Get path to call in relation to parent container chain of subroutes/route/prefixes, 
        including variables and exposing as (params, func) '''
        # p_params, p_func = self._parent._get_path()
        #TODO

    def _call_interface(self, parent:SubInterface, con:None|Entity_Interface, *args,**kwargs):
        ''' Match func based on context. connection may or may not exist (if not assume internal?)  '''
        print(self,parent,con)

        #DO these two need to be different? If I'm inheriting a connection?


api_item = _api_item._init_wrapper

import time


if __name__ == '__main__':
    
    class shared_subinterface(SubInterface):
        _path    = '/cmds/'
        

        def call_ping(self,con):
            return con.cmds.ping()

        @api_item('/ping')
        def ping(self, con:Entity_Interface)->str:
            ''' Defines IO and Fallback'''
            raise Exception('FALLBACK ENCOUNTERED')

        @ping.Get(key = 'all_get') #Blank, Thus filter should always be encounterd
        def _ping(self, con:Entity_Interface)->str:
            return { 'cmd' : CALLS.GET.value,  'name' : con.name,  'state' : con.con_state }

        @ping.Post(key = 'all_set') #Blank, Thus filter should always be encounterd
        def _ping(self, con:Entity_Interface):
            return { 'cmd' : CALLS.POST.value,  'name' : con.name,  'state' : con.con_state }

        @ping.Patch(key = 'all_patch') #Blank, Thus filter should always be encounterd
        def _ping(self, con:Entity_Interface):
            return { 'cmd' : CALLS.PATCH.value,  'name' : con.name,  'state' : con.con_state }

        @ping.Delete(key = 'all_del') #Blank, Thus filter should always be encounterd
        def _ping(self, con:Entity_Interface):
            return { 'cmd' : CALLS.DELETE.value,  'name' : con.name,  'state' : con.con_state }
    
    Role_Mapping = {}

    class Undeclared(Entity_Interface):
        role         = Role.UNDECLARED
        role_mapping = Role_Mapping


    class A(Entity_Interface):
        #Type Declarations:
        role         = Role.A
        role_mapping = Role_Mapping

        #SubInterfaces:
        cmds = shared_subinterface
        
        #Connections (Single):
        ext_con : 'B'

        #Test Funcs:
        def add_con(self,ip,port):
            con = Connection(ip=ip,port=port)
            self.ext_con = B.as_connection(con)
        def run_test(self):
            return self.ext_con.cmds.ping()


    class B(Entity_Interface):
        #Type Declarations:
        role         = Role.B
        role_mapping = Role_Mapping
        
        #SubInterfaces:
        cmds = shared_subinterface
        
        #Connections (Single):
        ext_con : A

        #Test Funcs:
        def add_con(self,ip,port):
            con = Connection(ip=ip,port=port)
            self.ext_con = A.as_connection(con)
        def run_test(self):
            return self.ext_con.cmds.ping()
    
    def test0():
        a = A()
        a.add_con(ip = 'localhost', port = '3000')
        a.run_test()
    test0()

    def test1():
        import argparse
        import sys
        parser = argparse.ArgumentParser()
        parser.add_argument('inst'       , default = None)
        parser.add_argument('wait'       , default = 5)
        parser.add_argument('try_delay'  , default = 5)
        parser.add_argument('this_ip'    , default = 'localhost')
        parser.add_argument('this_port'  , default = None)
        parser.add_argument('other_ip'   , default = 'localhost')
        parser.add_argument('other_port' , default = None)

        args,_ = parser.parse_known_args(sys.argv)

        match args.inst:
            case None:
                ... #call subprocess to create both instances and exit
                
                sys.exit()

            case 'a': prim = A()
            case 'b': prim = B()

        #Start the server with A as a primary, create connection to other in {wait} seconds
        # Close with message that was responded if successfull

        #Fastapi start
        #Fastapi server attach a.subgroutes
        
        time.sleep(args.wait)
        res = None
        prim.add_con(ip = args.other_ip,  port = args.other_port)
        while res is not None:
            time.sleep(args.try_delay)
            try: 
                res = prim.run_test()
            except Exception as e:
                print(e)
        print(res)
