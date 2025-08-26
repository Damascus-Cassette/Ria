
from enum import Enum
from inspect import isclass
import fastapi
from types import FunctionType

class Int(Enum):
    ''' If a call comes from an internal interface '''
    
class Ext(Enum):
    ''' If a call comes from an external/connection interface '''    
    
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

    def get(self):
        ...
    def post(self):
        ...
    def patch(self):
        ...
    def delete(self):
        ...

from typing import Self
class Entity_Interface():
    ''' An entity interface that can be started in either a local or connection mode. Asc with a role'''
    is_local   : bool       = True
    connection : Connection = None
    con_state  : State     = State.UNTRUSTED
    connection_handler : 'Ext_Interface_Handlder'
    @classmethod
    def as_connection(cls,connection:Connection)->Self:
        new = cls.__new__()
        new.connection = connection
        new.con_state  = State.UNTRUSTED
        return new

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

    def __new__(self):
        ''' Place Object's Sub IO  here '''
        for k,v in self._subinterfaces_uninit():
            setattr(self,k,v(self))

    def __init__(self):
        self.is_local = True
        self.connection_handler = Ext_Interface_Handlder(self)
        self.router             = fastapi.APIRouter()
        for k,v in self._subinterfaces():
            v._register(self.router)


class SubInterface():
    ''' In short these interfaces should know all routed functions & their interfaces
    Also 
    '''
    _router      : fastapi.APIRouter | None 

    def __init__(self,parent:Entity_Interface):
        self.parent = parent

    def _api_items(self):
        for k in dir(self):
            v = getattr(self,k)
            if isinstance(v,api_item):
                yield k,v

    def _register(self,router:fastapi.APIRouter):
        self._router = self.make_router()
        for k,v in self._api_items():
            v._register(router)
        router.add_route(self._router)

    def make_router(self,):
        return fastapi.APIRouter()


class Ext_Interface_Handlder():
    ''' Singleton per primary entity that handles creating and merging connections based on roles as well as registering complete routes '''
    ... #TODO
    
    def __init__(self, entity: Entity_Interface):
        self.entity = entity
    

from functools import wraps

class _routed_func():
    def __init__(self,mode:CALLS, func, filter):
        self.mode   = mode
        self.filter = filter
        self.func   = func
        
    def __call__(self, *args, **kwargs):
        return self.func(*args,**kwargs)
    
    def match(self,*args,**kwargs):
        return self.filter(*args,**kwargs)

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
        self.func         = func
        self._path        = path
        self._fapi_args   = args
        self._fapi_kwargs = kwargs
        self._methods     = []

    @classmethod
    def _init_wrapper(cls,path,*args,**kwargs):
        def wrapper(func):
            cls(func,path,*args,**kwargs)
        return wrapper
    
    def __call__(self, *args,**kwargs):
        self._internal_call_interface(*args,**kwargs)

    def _register(self,router:fastapi.APIRouter)->None:
        args, kwargs = self._api_route_args()
        router.add_api_route(self._api_route_args())
        
    def _api_route_arg(self)->tuple[tuple,dict]:
        ''' Pass in the arguments of path and such '''
        wrapped = self._external_call_interface()
        path = self._path

        return (path, wrapped) + self._fapi_args, {'methods':self._methods} | self._fapi_kwargs
    
    def _get_path():
        ''' Get path in relation to parent container chain of subroutes/route/prefixes '''
        ...

    def _external_call_interface():
        ''' This is the External header function '''
        ...

    def _internal_call_interface():
        ''' This is the Internal header function '''
        ...

    def _produce_filter(Self, self_role:Role, self:Int|Ext, requester:Int|Ext|Role, requester_state:State):
        def _filter():
            return True #TODO: Filtering
        return _filter

    def _wrapper(_self, 
            mode            :CALLS               , 
            key             :str          = None , #Allows bypassing of wrapper in calling, for local calls and debugging
            self_role       :Role         = None , 
            self            :Int|Ext      = None , 
            requester       :Int|Ext|Role = None , 
            requester_state :State        = None ,
            ):
        ''' Add an item to the wrapper with above arguments '''
        def wrapper(func):
            if isinstance(func,_routed_func):
                func = func.func
            inst = _routed_func(
                        Mode   = mode, 
                        func   = func,
                        filter = _self._produce_filter(
                            self_role       = self_role, 
                            self            = self, 
                            requester       = requester, 
                            requester_state = requester_state,
                            )
                        )
            _self._routes.append(inst)
            if key:
                setattr(self,key,inst)
            return inst
        return wrapper

    @wraps(_wrapper)    
    def Get(self,*args,**kwargs): 
        if CALLS.GET.value not in self._methods: 
            self._methods.append(CALLS.Get.value)
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
        return self._wrapper(CALLS.DELETE,*args,**kwargs)
        if CALLS.DELETE.value not in self._methods: 
            self._methods.append(CALLS.DELETE.value)

api_item = _api_item._init_wrapper

import time



class shared_subinterface(SubInterface):
    
    def call_ping(self,con):
        return con.cmds.ping()

    @api_item('ping')
    def ping(self, con:Entity_Interface):
        ''' Defines IO and Fallback'''
        raise Exception('FALLBACK ENCOUNTERED')

    @ping.Get(key = 'all_get') #Blank, Thus filter should always be encounterd
    def ping(self, con:Entity_Interface):
        return { 'cmd' : CALLS.GET.value,  'name' : con.name,  'state' : con.con_state }

    @ping.POST(key = 'all_set') #Blank, Thus filter should always be encounterd
    def ping(self, con:Entity_Interface):
        return { 'cmd' : CALLS.POST.value,  'name' : con.name,  'state' : con.con_state }

    @ping.Patch(key = 'all_patch') #Blank, Thus filter should always be encounterd
    def ping(self, con:Entity_Interface):
        return { 'cmd' : CALLS.PATCH.value,  'name' : con.name,  'state' : con.con_state }

    @ping.Delete(key = 'all_del') #Blank, Thus filter should always be encounterd
    def ping(self, con:Entity_Interface):
        return { 'cmd' : CALLS.DELETE.value,  'name' : con.name,  'state' : con.con_state }
    

class A(Entity_Interface):
    role = Role.A
    cmds = shared_subinterface
    ext_con = 'B'


    def add_con(self,ip,port):
        con = Connection(ip=ip,port=port)
        self.ext_con = B.as_connection(con)
    def run_test(self):
        return self.ext_con.cmds.ping()

class B(Entity_Interface):
    role = Role.B
    cmds = shared_subinterface
    ext_con = A

    def add_con(self,ip,port):
        con = Connection(ip=ip,port=port)
        self.ext_con = A.as_connection(con)
    def run_test(self):
        return self.ext_con.cmds.ping()
    

if __name__ is '__main__':
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
    
