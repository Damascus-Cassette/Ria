
from functools import partial, wraps
from enum      import Enum
from inspect   import isclass, signature as _sig
from typing    import Self
from types     import FunctionType,LambdaType
from contextvars import ContextVar

class _UNSET():...
class PRIMARY():...
class Entity_Int: ''' Internal for type Anno '''
class Entity_Ext: ''' External for type Anno '''

class Command(Enum):
    GET    = 'GET'
    POST   = 'POST'
    PATCH  = 'PATCH'
    DELETE = 'DELETE'

context_pool = ContextVar('entity_pool',default=None)


class _method():
    ''' Local inst-method cls '''
    def __get__(self, inst, inst_cls):
        if inst is None:
            return self
        else:
            return partial(self,inst)

    def __init__(self, func):
        self.func = func
    
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class _ol_func_item():
    ''' Container for a function & it's evaluation '''

    def __init__(self,func,key=None,**kwargs):
        self.func          = func
        self.key           = key
        self.filter_kwargs = kwargs
        
    def execute(self, container, this_entity:Entity, other_entity:Entity, *args,**kwargs):
        return self.func(container,this_entity, other_entity, *args,**kwargs)

    def match(self,this_entity:Entity,other_entity:Entity):
        raise Exception('Child class expected to handle this')
    
    @classmethod
    def _wrapper(cls, parent, key=None, *args,**kwargs):
        ''' Wrapper to Intake info with resolve as:
            un-nest w/a
            attach to parent (OL_Container)
            return a _method[original_function] '''
        def wrapper[F](func:F)->F:

            if isinstance(func,(_ol_func_item_deliver,_ol_func_item_recieve)):
                func = func.func
            elif isinstance(func,OL_Container):
                func = func._origin_func
            
            inst = cls(func,*args,**kwargs)
            parent.add_func_container(inst)
            if key: parent.add_func_direct(key,inst)
            
            return _method(func)

        return wrapper

class _ol_func_item_recieve(_ol_func_item):
    ''' Ext -- calling -> Int '''

    def match(self,this_entity:'Entity_Int',other_entity:'Entity_Ext'):
        assert this_entity.Is_Int
        assert other_entity.Is_Ext
        ... #TODO

class _ol_func_item_deliver(_ol_func_item):
    ''' Int -- calling -> Ext '''
    
    def match(self,this_entity:'Entity_Ext',other_entity:'Entity_Int'):
        assert this_entity.Is_Ext
        assert other_entity.Is_Int
        ... #TODO

from copy import copy

class _def_dict_list(dict):
    def __missing__(self,key):
        self[key] = res = []
        return res

class OL_Container():
    ''' OL func Container, ie a contextual router that contains _ol_func_items. 
    Must have 'view' made when instancing parent
    Prob way more effecient & safe than forcing partial or setting a context va every access '''

    def __init__(self, func, path, *args,**kwargs):
        self._origin_func = func
        self._path        = path
        self._f_args      = args
        self._f_kwargs    = kwargs
        self._container   = None
        self._reciever_functions  :_def_dict_list[str,_ol_func_item_recieve] = _def_dict_list()
        self._delivery_functions  :_def_dict_list[str,_ol_func_item_deliver] = _def_dict_list()

    @classmethod
    def _on_new(cls,inst):
        ''' Utility, Call on new item to setup 'views' (local shallow copies w/ one var change) '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if isinstance(v,cls):
                if not (v._container is inst): 
                    setattr(inst,k,v._view(inst))

    def _view(self,container):
        new = copy(self)
        new._container = container
        return new
    
    def __call__(self, other_entity, request=None, *args, **kwargs):
        ''' Unfortunatly does require other entity to be declared as far as I can tell '''
        this_entity = self._container.Root_Entity
        recieving   = this_entity.Is_Internal

        if recieving:
            assert request is not None 
            func = self.find_recieving (this_entity,other_entity,request)
            return func(self._container, this_entity, other_entity, *args, **kwargs)
        else: 
            func = self.find_delivering(this_entity,other_entity)
            return func(self._container, this_entity, other_entity, request, *args, **kwargs)
        
    def add_func_container(self,func_item:_ol_func_item):
        if   isinstance(func_item,_ol_func_item_deliver):
            self._delivery_functions.append(func_item)
        elif isinstance(func_item,_ol_func_item_recieve):
            self._reciever_functions.append(func_item)

    def add_func_direct(self,key,func):
        if hasattr(self,key):
            raise Exception(f'{self} SETUP ERROR: "{key}" already in use by {getattr(self,key)}' )
        setattr(self,key,func)

    def _register(self, router, entity_pool, args=None, kwargs=None):
        ''' Registers reciever functions to contextual entity pool '''
        
        for mode, func_list in self._reciever_functions.items():
            face_ol_item : _ol_func_item_recieve = func_list[0] #First func in list is used to define the interface.
            # _args,_kwargs = face_func._api_route_args(self._container._root_entity, self._container, self, router, *args, **kwargs)
            _args,_kwargs = self._api_router_args_(face_ol_item, entity_pool, mode, args, kwargs)
            router.add_api_route(*_args,**_kwargs)

    def _api_router_args_(self, face_ol_item:_ol_func_item_recieve, entity_pool, mode:Enum, args=None, kwargs=None)->tuple[tuple,dict]:
        self._api_rout_wrapped_func_(face_ol_item,entity_pool)
        if kwargs is None: kwargs = {}
        if args   is None: args   = tuple()

        wrapped = self._api_route_wrapped_func_(face_ol_item, entity_pool)
        path    = self._path

        return (path, wrapped) + self._f_args + args, {'methods':[mode.value]} | self._f_kwargs | kwargs

    def _api_route_wrapped_func_(self, face_ol_item:_ol_func_item_recieve, entity_pool)->FunctionType:
        func = face_ol_item.func
        sig = _sig()

        entity_pool = context_pool.get()
        
        def wrapped(request:Request,*args,**kwargs):
            ext_entity = entity_pool.ensure_request_entity(request)
            return self(ext_entity,request,*args,**kwargs)
        
        wrapped.__name__      = func.__name__
        wrapped.__signature__ = sig.replace(
            parameters        = [_sig(wrapped).parameters['request'], *list(sig.parameters.values())[2:]], 
            return_annotation = sig.return_annotation
            )
        #Spoof signature to that of wrapped_request + original for fastapi introspection
        return wrapped
    
    @wraps(_ol_func_item_recieve._wrapper)
    def Get_Recieve(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.GET,*args,**kwargs)

    @wraps(_ol_func_item_deliver._wrapper)
    def Get_Deliver(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.GET,*args,**kwargs)

    @wraps(_ol_func_item_recieve._wrapper)
    def Post_Recieve(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.POST,*args,**kwargs)

    @wraps(_ol_func_item_deliver._wrapper)
    def Post_Deliver(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.POST,*args,**kwargs)

    @wraps(_ol_func_item_recieve._wrapper)
    def Patch_Recieve(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.PATCH,*args,**kwargs)

    @wraps(_ol_func_item_deliver._wrapper)
    def Patch_Deliver(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.PATCH,*args,**kwargs)

    @wraps(_ol_func_item_recieve._wrapper)
    def Delete_Recieve(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.DELETE,*args,**kwargs)

    @wraps(_ol_func_item_deliver._wrapper)
    def Delete_Deliver(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.DELETE,*args,**kwargs)


from fastapi import FastAPI, APIRouter,Request

class Interface_Base():
    Router_Subpath : str

    def __new__(self,):
        OL_Container._on_new(self)
        Interface_Base._on_new(self)
    
    def __init__(self, parent : 'Entity'|'Interface_Base'):
        self._parent = parent
        self._Root_Entity = parent._Root_Entity

    @staticmethod
    def _on_new(inst):
        ''' Intialize Interface Structure '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if not isclass(v):
                continue
            if issubclass(v,Interface_Base):
                setattr(inst,k,v(inst))
    
    @staticmethod
    def _iter_insts(inst):
        ''' Intialize Interface Structure '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if isclass(v):
                continue
            if issubclass(v.__class__,Interface_Base):
                yield v

    def _create_local_router(self):
        return APIRouter()
    
    def _attach_local_router(self,local_router:APIRouter,entity_pool,args=None,kwargs=None):        
        for ol_func in OL_Container._iter_insts(self):
            ol_func._register(local_router,entity_pool,args,kwargs)
        for subinterface in Interface_Base._iter_insts(self):
            subinterface : Self
            subinterface._register(local_router,entity_pool,args,kwargs)
        return local_router
    
    def _register(self, parent_router, entity_pool, args=None, kwargs=None):
        local_router = self._attach_local_router(self._create_local_router(),entity_pool,args,kwargs)
        parent_router.add_api_route(local_router,getattr(self,'Router_Subpath',''))
        return parent_router

import time

REQ_KEY_MAPPING : dict[str,LambdaType] = {
    'url.path'    : lambda request: request.url.path    ,
    'url.port'    : lambda request: request.url.port    ,
    'url.scheme'  : lambda request: request.url.scheme  ,
    'client.host' : lambda request: request.client.host ,
    'client.port' : lambda request: request.client.port ,
    'Intake_Time' : lambda request: time.time()         ,
}
#TODO: Cookies & verification


class _Entity_Data_Foreign():
    ''' Foreign representation of a data entity, 
    constructed from entity data class & compared to on signed connections
    instanced from header data
    '''

    _keys : dict

    @classmethod
    def construct(cls, other_cls:'Entity_Data'):
        ''' Intake what keys & attributes should be pulled onto this foreign rep '''
        publish_dict    = other_cls._Foreign_Publish_Def | other_cls.Foreign_Publish
        request_parsing = other_cls._Foreign_In_Req_Def  | other_cls.Foreign_In_Req 
        
        assert not any([x for x in publish_dict.values()    if x.startswith('_')])
        assert not any([x for x in request_parsing.values() if x.startswith('_')])
        assert not any([x for x in request_parsing.keys()   if not x in REQ_KEY_MAPPING.keys()])
            #TODO: Logically could be much simpler, brain not working atm
            #TODO: Also test to protect for certain header keys?

        slots = tuple(publish_dict.values()) + tuple(request_parsing.values())

        return type(f'{cls.__name__}.foreign_data',(cls,),{'_keys':publish_dict,'_request_intake':request_parsing, '__slot__':slots})
    
    def __init__(self):
        ...
    
    def _populate_from_enity_data_(self,entity_data:'Entity_Data'):
        for k,v in self._keys:
            setattr(self, k, getattr(entity_data,k,'_UNSET'))

    def _populate_from_header_data_(self,request):
        ''' Inverse of Entity_Data._create_header_data_ that also gets some from info from the req '''

        for k,v in self._keys.items():
            setattr(self,v,request.header.get(k))
            #key inverse of publishing

        for k,v in self._request_intake():
            setattr(self,v,REQ_KEY_MAPPING[k](request))
            

    def _post_to_header_data_(self,source_entity,toward_entity)->dict:
        ''' Create header data dictionary, Defeaults '''
        res = {}

        for k,v in self._keys:
            res[v] = getattr(self,k,'_UNSET')
            
        return res
        

class Entity_Data:
    '''Contain local-data of entities from intaking _Entity_Data_Foreign items
    Constructs _Entity_Data_Foreign representation and compares self to it when identifying and merging
    Has protected keys that cannot be set, but can be published
    '''

    _Foreign_Base = _Entity_Data_Foreign
    _Foreign : _Entity_Data_Foreign
    
    def __init_subclass__(cls):
        cls._Foreign = cls._Foreign_Base.construct(cls) 

    _entity : 'Entity'
    
    def __init__(self,entity:'Entity'):
        self._entity = entity


    #Request -> Foreign[Incoming]
    Foreign_In_Req       : dict[str,LambdaType] = {}
    _Foreign_In_Req_Def  : dict[str,LambdaType] = {}
        #Local : Foreign

    #Local -> Foreign[Outgoing/Incoming] <- Request
    Foreign_Publish      : dict[str,str]        = {}
    _Foreign_Publish_Def : dict[str,str]        = {}
        #_Entity_Data_Foreign from self, before converting that to headers
        #TODO: future support for lambda & type casting
        #Local : Foreign

    #Determining (Local == Foreign) during Foreign[Incoming] -> ?Local
    Foreign_Match_keys   : dict[str,str|LambdaType]|FunctionType
        #Local : Foreign

    #Foreign[Incoming] -> Local 
    Foreign_Intake       : dict[str,str]|FunctionType   = {}
    _Foreign_Intake_Def  : dict[str,str]                = {} 
        #Local : Foreign
    

    def _compare_to_foreign_(self,request,foreign:_Entity_Data_Foreign)->bool:
        ''' Interpret foreign data corrisponds to local entity via self.Foreign_Match_Keys
        Local-Left for type comparison priority
        #TODO: Type casting right on foreign
        #TODO: Compare Unset Rules?
        #TODO: False Assumption instead of Truth Assumption?
        '''
        
        assert len(self.Foreign_Match_keys)

        if isinstance(self.Foreign_Match_keys, FunctionType):
            return self.Foreign_Match_keys(foreign)
        
        for k,v in self.Foreign_Match_keys.items():
            local_val   = getattr(self,k,_UNSET)
            if local_val is _UNSET: return False
            if isinstance(v,(FunctionType,LambdaType)):
                if not v(request, foreign, local_val): 
                    return False
            else:
                foreign_val = getattr(foreign,v,_UNSET)
                if foreign_val is _UNSET: return False
                if not local_val == foreign_val:
                    return False

        return True    
        

    def _update_from_foreign_(self,foreign:_Entity_Data_Foreign)->None:
        for k,v in (self._Foreign_Intake_Def | self.Foreign_Intake).keys():
            assert not k.startswith('_')
            
            if isinstance(v,(FunctionType,LambdaType)):
                f_val = v(foreign)
            else:
                f_val = getattr(foreign,v,_UNSET) 

            setattr(self,v,f_val)
                    
        

class Entity_Pool:
    
    pool : list['Entity'] 
    
    ... #TODO

class Entity(Interface_Base):
    Entity_State          : Enum | _UNSET           = _UNSET
    Connection_State      : Enum | _UNSET | PRIMARY = _UNSET
    # Entity_Observed_Connection_State : dict[Enum]
        # What each connection assigns state to self w/a
        # Offset into connection?
    
    def __init__(self):
        self._Root_Entity = self

    @property
    def Is_Internal(self,): ... #TODO
    @property
    def Is_External(self,): ... #TODO
