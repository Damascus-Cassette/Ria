
from functools   import partial, wraps
from enum        import Enum
from inspect     import isclass, signature as _sig, iscoroutinefunction
from typing      import Self
from types       import FunctionType,LambdaType
from contextvars import ContextVar
from fastapi     import FastAPI, APIRouter,Request
from starlette.responses import Response

from copy import copy
import time 

class _UNSET():...
class PRIMARY():...
class Entity_Int: ''' Internal for type Anno '''
class Entity_Ext: ''' External for type Anno '''

class _def_dict_list(dict):
    def _web_repr_(self)->dict:
        res = {}
        for k,v in self.items():
            res[k] = ls = []
            for e in v:
                ls.append(getattr(e,'_web_repr_',e.__repr__()))
        return res
    
    def _each_subitem_(self):
        for k,v in self.items():
            for e in v:
                yield k,e
    
    def __missing__(self,key):
        self[key] = res = []
        return res
    
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

    def __init__(self,func,key=None,filter=True):
        self.func          = func
        self.key           = key
        self.filter        = filter
        
    def execute(self, container, this_entity:'Entity', other_entity:'Entity', *args,**kwargs):
        return self.func(container,this_entity, other_entity, *args,**kwargs)

    def match(self,mode:Command,this_entity:'Entity',other_entity:'Entity',request:Request):
        raise Exception('Child class expected to handle this')
    
    @classmethod
    def _wrapper(cls, parent, mode, key=None, *args,**kwargs):
        ''' Wrapper to Intake info with resolve as:
            un-nest w/a
            attach to parent (_OL_Container)
            return a _method[original_function] '''
        def wrapper[F](func:F)->F:

            if isinstance(func,(_ol_func_item_deliver,_ol_func_item_recieve)):
                func = func.func
            elif isinstance(func,_OL_Container):
                func = func._origin_func
            
            inst = cls(func,*args,**kwargs)
            parent.add_func_container(mode,inst)
            if key: parent.add_func_direct(key,inst)
            
            return _method(func)

        return wrapper

class _ol_func_item_recieve(_ol_func_item):
    ''' Ext -- calling -> Int '''

    def __call__(self, *args, **kwds):
        return self.func(*args, **kwds)
    
    def match(self,mode:Command,this_entity:'Entity',other_entity:'Entity',request:Request):
        assert this_entity.Is_Local_State is Entity_Int
        assert other_entity.Is_Local_State is Entity_Ext

        if isinstance(self.filter, bool):
            return self.filter
        return self.filter(mode,this_entity,other_entity,request)


class _ol_func_item_deliver(_ol_func_item):
    ''' Int -- calling -> Ext '''
    
    def __call__(self, *args, **kwds):
        return self.func(*args, **kwds)

    # def match(self,this_entity:'Entity_Ext',other_entity:'Entity_Int'):
    def match(self,mode:Command,this_entity:'Entity',other_entity:'Entity'):
        assert this_entity.Is_Local_State is Entity_Ext
        assert other_entity.Is_Local_State is Entity_Int

        if isinstance(self.filter, bool):
            return self.filter
        return self.filter(mode,this_entity,other_entity)


class _OL_Container():
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
    def _wrapper(cls,*args,**kwargs):
        def wrapper(func):
            return cls(func,*args,**kwargs)
        return wrapper
    

    @classmethod
    def _on_new(cls,inst):
        ''' Utility, Call on new item to setup 'views' (local shallow copies w/ one var change) '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if isinstance(v,cls):
                if not (v._container is inst): 
                    setattr(inst,k,v._view(inst))

    @staticmethod
    def _iter_insts(inst):
        ''' Intialize Interface Structure '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if isclass(v):
                continue
            if issubclass(v.__class__,_OL_Container) or (v.__class__ is _OL_Container):
                yield v

    def _view(self,container):
        new = copy(self)
        new._container = container
        return new
    
    def __call__(self, mode, other_entity, request=None, *args, **kwargs):
        ''' Unfortunatly does require other entity to be declared as far as I can tell '''
        #TODO: Convert above to have _ prefixes
        this_entity = self._container._Root_Entity
        recieving   = this_entity.Is_Local_State is Entity_Int
    
        if recieving:
            assert request is not None
            func = self.find_recieving (mode,this_entity,other_entity,request)
            return func(self._container, this_entity, other_entity, *args, **kwargs)
        else: 
            # assert raw_path is not None
            raw_path = self._get_raw_path_()
            func = self.find_delivering(mode, this_entity, other_entity)
            return func(self._container, this_entity, other_entity, raw_path, *args, **kwargs)
    
    def _get_raw_path_(self):
        return f'{self._container._get_raw_path_()}/{self._path}'

    def find_recieving(self, mode, this_entity,other_entity,request):
        # raise Exception('FIND RECIEVING' , mode, this_entity, other_entity)
        for item in self._reciever_functions[mode]:
            item : _ol_func_item_recieve
            if item.match(mode, this_entity, other_entity, request):
                return item
        raise Exception('COULD NOT FIND MATCHING ENDPOINT WITH:', mode, this_entity ,other_entity )
        # return self._origin_func
            
    def find_delivering(self, mode, this_entity,other_entity):
        for item in self._delivery_functions[mode]:
            item : _ol_func_item_deliver
            if item.match(mode, this_entity ,other_entity):
                return item
        raise Exception('COULD NOT FIND MATCHING DELIVERY POINT WITH:', mode, this_entity ,other_entity )
        # return self._origin_func


    def add_func_container(self,mode,func_item:_ol_func_item):
        if   isinstance(func_item,_ol_func_item_deliver):
            return self._delivery_functions[mode].append(func_item)
        elif isinstance(func_item,_ol_func_item_recieve):
            print('')
            return self._reciever_functions[mode].append(func_item)
        raise Exception('COULD NOT INTAKE', mode, func_item.func.__name__)

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
        if kwargs is None: kwargs = {}
        if args   is None: args   = tuple()

        wrapped = self._api_route_wrapped_func_(face_ol_item, mode, entity_pool)
        path    = self._path

        return (path, wrapped) + self._f_args + args, {'methods':[mode.value]} | self._f_kwargs | kwargs

    def _api_route_wrapped_func_(self, face_ol_item:_ol_func_item_recieve, mode, entity_pool)->FunctionType:
        func = face_ol_item.func
        sig = _sig(func)
        
        if not iscoroutinefunction(func):
            def wrapped(request:Request,*args,**kwargs):
                ext_entity = entity_pool._ensure_incoming_entity_(request)
                return self(mode, ext_entity, request, *args,**kwargs)
        else:
            async def wrapped(request:Request,*args,**kwargs):
                ext_entity = entity_pool._ensure_incoming_entity_(request)
                return await self(mode, ext_entity, request, *args,**kwargs)
        
        #Strongly need to consider moving _ensure_incoming_entity_ to middleware to avoid multiple entities spawning from the different 'threads'

        wrapped.__name__      = func.__name__
        wrapped.__signature__ = sig.replace(
            parameters        = [_sig(wrapped).parameters['request'], *list(sig.parameters.values())[3:]], 
            return_annotation = sig.return_annotation
            )
        #Spoof signature to that of wrapped_request + original for fastapi introspection
        return wrapped
    

    @wraps(_ol_func_item_recieve._wrapper)
    def Get_Endpoint(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.GET,*args,**kwargs)

    @wraps(_ol_func_item_recieve._wrapper)
    def Post_Endpoint(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.POST,*args,**kwargs)

    @wraps(_ol_func_item_recieve._wrapper)
    def Patch_Endpoint(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.PATCH,*args,**kwargs)

    @wraps(_ol_func_item_recieve._wrapper)
    def Delete_Endpoint(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.DELETE,*args,**kwargs)


    @wraps(_ol_func_item_deliver._wrapper)
    def Get_Send(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.GET,*args,**kwargs)

    @wraps(_ol_func_item_deliver._wrapper)
    def Post_Send(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.POST,*args,**kwargs)

    @wraps(_ol_func_item_deliver._wrapper)
    def Patch_Send(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.PATCH,*args,**kwargs)

    @wraps(_ol_func_item_deliver._wrapper)
    def Delete_Send(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.DELETE,*args,**kwargs)

    # @wraps(_ol_func_item._wrapper)
    # def Default(self, mode:Command, is_send = False, *args, **kwargs):
    #     if isinstance(mode, str):
    #         mode = Command(mode)
    #     def wrapper(func):
    #         if is_send:
    #             _ol_func_item_deliver._wrapper(parent=self,mode=Command.DELETE,*args,**kwargs)(func)
    #         else:
    #             _ol_func_item_recieve._wrapper(parent=self,mode=Command.DELETE,*args,**kwargs)(func)
    #         return self
    #     return wrapper    

    def Send_Get(self,sending_entity,*args,**kwargs):
        return self(Command.GET, sending_entity, *args, **kwargs)
    
    def Send_Post(self,sending_entity,*args,**kwargs):
        return self(Command.POST, sending_entity, *args, **kwargs)
    
    def Send_Patch(self,sending_entity,*args,**kwargs):
        return self(Command.PATCH, sending_entity, *args, **kwargs)
    
    def Send_Delete(self,sending_entity,*args,**kwargs):
        return self(Command.DELETE, sending_entity, *args, **kwargs)

OL_Container = _OL_Container._wrapper

class Interface_Base():
    Router_Subpath : str

    def __new__(cls,*args,**kwargs):
        new = super().__new__(cls)
        _OL_Container._on_new(new)
        Interface_Base._on_new(new)
        return new
    
    def __init__(self, parent ): # : 'Entity'|'Interface_Base'):
        self._parent = parent
        if getattr(parent,'_Root_Entity',None) is Self:
            self._Root_Entity = parent
        else:
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

    def _get_raw_path_(self):
        if (self._Root_Entity is Self) or (self._Root_Entity is self):
            return getattr(self,'Router_Subpath','')
        else: 
            return self._Root_Entity._get_raw_path_() + getattr(self,'Router_Subpath','')

    def _create_local_router(self):
        return APIRouter()
    
    def _attach_local_router(self,local_router:APIRouter,entity_pool,args=None,kwargs=None):        
        for ol_func in _OL_Container._iter_insts(self):
            ol_func._register(local_router,entity_pool,args,kwargs)
        for subinterface in Interface_Base._iter_insts(self):
            subinterface : Self
            subinterface._register(local_router,entity_pool,args,kwargs)
        return local_router
    
    def _register(self, parent_router, entity_pool, args=None, kwargs=None):
        local_router = self._attach_local_router(self._create_local_router(),entity_pool,args,kwargs)
        parent_router.include_router(local_router,prefix = getattr(self,'Router_Subpath', ''))
        return parent_router

REQ_KEY_MAPPING : dict[str,LambdaType] = {
    'url.path'    : lambda request: request.url.path    ,
    'url.port'    : lambda request: request.url.port    ,
    'url.scheme'  : lambda request: request.url.scheme  ,
    'client.host' : lambda request: request.client.host ,
    'client.port' : lambda request: request.client.port ,
    'Intake_Time' : lambda request: time.time()         ,
}
#TODO: Cookies & verification

import requests

class Connection():
    ''' Connection object created from request. 
    Containes wrapped methods to interact with a connection 
    #TODO: Rewrite when I understand more
    #TODO: Sec. middle-ware reqs here '''
    
    def __init__(self, parent:'Entity_Data', **kwargs):
        self.entity_data = parent
        self._update_from_kwargs_(**kwargs)

    port : str      = None
    host : str      = None
    user : str|None = None
    pswd : str|None = None
    mode : str      = 'http://'

    def _update_from_request_(self,request:Request):
        self.host = request.client.host
        self.port = request.client.port

    def _update_from_kwargs_(self,**kwargs):
        for k,v in kwargs.items():
            if hasattr(self,k) and k in ['port', 'host', 'user', 'pswd', 'mode']:
                setattr(self,k,v)

    def _cast_responce(self, res : requests.Response)->Request:
        if isinstance(res,Response): return res
        return Response(
            content     = res.content,
            status_code = res.status_code,
            headers     = res.headers,
            # media_type  = res.media_type,
        )
        

    def _domain(self)->str:
        assert not (self.mode is None)
        assert not (self.host is None)
        assert not (self.port is None)

        return self.mode + self.host+':'+self.port

    def get(self, from_entity:'Entity', path:str, _raw_responce=False, **kwargs):
        header_data = from_entity.entity_data._Foreign(from_entity.entity_data)._post_to_header_data_(from_entity) | self.entity_data._outgoing_header_data_(from_entity)
        if self.user: res = requests.get(self._domain()+path, params=kwargs, auth=(self.user,self.pswd), headers=header_data)
        else:         res = requests.get(self._domain()+path, params=kwargs, headers=header_data)
        if _raw_responce: return res
        else:             return res.content
        
    def patch(self, from_entity:'Entity', path:str, _raw_responce=False, **kwargs):
        header_data = from_entity.entity_data._Foreign(from_entity.entity_data)._post_to_header_data_(from_entity) | self.entity_data._outgoing_header_data_(from_entity)
        if self.user: res = requests.patch(self._domain()+path, params=kwargs, auth=(self.user,self.pswd), headers=header_data)
        else:         res = requests.patch(self._domain()+path, params=kwargs, headers=header_data)
        if _raw_responce: return res
        else:             return res.content

    def post(self, from_entity:'Entity', path:str, _raw_responce=False, **kwargs):
        header_data = from_entity.entity_data._Foreign(from_entity.entity_data)._post_to_header_data_(from_entity) | self.entity_data._outgoing_header_data_(from_entity)
        if self.user: res = requests.post(self._domain()+path, params=kwargs, auth=(self.user,self.pswd), headers=header_data)
        else:         res = requests.post(self._domain()+path, params=kwargs, headers=header_data)
        if _raw_responce: return res
        else:             return res.content

    def delete(self, from_entity:'Entity', path:str, _raw_responce=False, **kwargs):
        header_data = from_entity.entity_data._Foreign(from_entity.entity_data)._post_to_header_data_(from_entity) | self.entity_data._outgoing_header_data_(from_entity)
        if self.user: res = requests.delete(self._domain()+path, params=kwargs, auth=(self.user,self.pswd), headers=header_data)
        else:         res = requests.delete(self._domain()+path, params=kwargs, headers=header_data)
        if _raw_responce: return res
        else:             return res.content

    def put(self, from_entity:'Entity', path:str, data, _raw_responce=False, **kwargs):
        header_data = from_entity.entity_data._Foreign(from_entity.entity_data)._post_to_header_data_(from_entity) | self.entity_data._outgoing_header_data_(from_entity)
        if self.user: res = requests.put(self._domain()+path, params=kwargs,data=data, auth=(self.user,self.pswd), headers=header_data)
        else:         res = requests.put(self._domain()+path, params=kwargs,data=data, headers=header_data)
        if _raw_responce: return res
        else:             return res.content

    #TODO: Convert to async requests.

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
    
    def __init__(self,populate_from=None):
        if not populate_from:
            ...
        elif isinstance(populate_from,Request):
            self._populate_from_header_data_(populate_from)
        else:
            self._populate_from_entity_data_(populate_from)
    
    def _populate_from_entity_data_(self,entity_data:'Entity_Data'):
        for k,v in self._keys:
            setattr(self, k, getattr(entity_data,k,'_UNSET'))

    def _populate_from_header_data_(self,request):
        ''' Inverse of Entity_Data._create_header_data_ that also gets some from info from the req '''

        for k,v in self._keys.items():
            setattr(self,v,request.header.get(k))
            #key inverse of publishing

        for k,v in self._request_intake.items():
            setattr(self,v,REQ_KEY_MAPPING[k](request))
            
    def _post_to_header_data_(self,from_entity): #$toward_entity)->dict:
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
    _Foreign      : _Entity_Data_Foreign
    
    def __init_subclass__(cls):
        cls._Foreign = cls._Foreign_Base.construct(cls) 

    _entity : 'Entity'
    
    def __init__(self,entity:'Entity'):
        self._entity = entity
        self.Connection = Connection(self)

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
    
    def _outgoing_header_data_(self,from_entity:'Entity')->dict:
        ''' Add specific header info for an outgoing request to this entity, 
        such as session tokens or private keys?  '''
        return {}

    def _compare_to_foreign_(self, request, foreign:_Entity_Data_Foreign)->bool:
        ''' Interpret foreign data corrisponds to local entity via self.Foreign_Match_Keys
        Local-Left for type comparison priority
        #TODO: Type casting right on foreign
        #TODO: Compare Unset Rules?
        '''
        
        if callable(self.Foreign_Match_keys):
            return self.Foreign_Match_keys(foreign)
        
        assert len(self.Foreign_Match_keys)

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
        

    def _update_from_foreign_(self, request:Request, foreign:_Entity_Data_Foreign)->None:
        self.Connection._update_from_request_(request)
        for k,v in (self._Foreign_Intake_Def | self.Foreign_Intake).keys():
            assert not k.startswith('_')
            
            if isinstance(v,(FunctionType,LambdaType)):
                f_val = v(foreign)
            else:
                f_val = getattr(foreign,v,_UNSET) 

            setattr(self,v,f_val)
        
class Entity_Pool:
    ''' Container for entities deduplicated by matching foreign-local entity data '''
    Default_Unsigned  : 'Entity'
    Default_Malformed : 'Entity'

    Entities          : list['Entity']
    Entity_Role_Dict  : dict[str,'Entity']

    Int : Enum
    Ext : Enum
    class _Int():...
    class _Ext():...

    ext_pool : _def_dict_list[str,list['Entity']]
    # int_pool : _def_dict_list[str,list['Entity']]

    #Entity that is started as internal
    Entity_Int_State  : Enum
    Default_Int_State : str|Enum

    #Entity that is started as external, observed information
    Entity_Ext_States  : Enum
    Default_Ext_State : str | Enum
    Entity_Con_States  : Enum
    Default_Con_State : str | Enum

    def __init_subclass__(cls):
        assert hasattr(cls , 'Entities'          )
        assert hasattr(cls , 'Default_Int_State' )
        assert hasattr(cls , 'Entity_Ext_States'  )
        assert hasattr(cls , 'Default_Ext_State' )
        assert hasattr(cls , 'Entity_Con_States'  )
        assert hasattr(cls , 'Default_Con_State' )

        cls.Entity_Role_Dict = {}

        for x in cls.Entities: 
            x.Entity_Pool_Type = cls

        entity_dict = {e.Entity_Role:e for e in cls.Entities}

        cls.Int = Enum('Int',entity_dict)
        cls.Ext = Enum('Ext',entity_dict)

    def __init__(self):
        self.ext_pool = _def_dict_list()

    def _ensure_incoming_entity_(self,request):
        role = request.headers.get('Entity_Role', default = None)
        if    role is None: 
            entity_type = self.Default_Unsigned
        else: entity_type = self._Entities.get(role, default = self.Default_Malformed)

        entity_data_type = entity_type.Entity_Data_Type._Foreign
        f_entity_data = entity_data_type()
        f_entity_data._populate_from_header_data_(request)

        for entity in self.ext_pool[entity_type.Entity_Role]:
            if entity.entity_data._compare_to_foreign_(request,f_entity_data):
                entity.entity_data._update_from_foreign_(request, f_entity_data)
                return entity
        
        new_entity = entity_type._init_from_foreign_(self,request,f_entity_data)
        self.ext_pool[entity_type.Entity_Role].append(new_entity)
        return new_entity
    

    def add_entity(self,entity:'Entity'):
        assert entity.Is_Local_State is Entity_Ext
        pool = self.ext_pool[entity.Entity_Role]
        if entity not in pool:
            self.ext_pool[entity.Entity_Role].append(entity)

class Entity(Interface_Base):
    ''' Combination Entity-Api-Interface '''
    Entity_Role      : str | Enum

    Is_Local_State   : Entity_Int | Entity_Ext 
    Entity_State     : Enum | _UNSET           = _UNSET
    Connection_State : Enum | _UNSET | PRIMARY = _UNSET
    
    Entity_Pool_Type : Entity_Pool = Entity_Pool
    entity_pool      : Entity_Pool
    
    Entity_Data_Type : Entity_Data = type('Entity_Data',(Entity_Data,),{})
    entity_data      : Entity_Data

    _Root_Entity     = Self

    def __init__(self):
        self._Root_Entity = self
        self.entity_data  = self.Entity_Data_Type(self) 

    @classmethod
    def _init_from_foreign_(cls, entity_pool, request, f_entity_data):
        new = cls()
        new.Is_Local_State = Entity_Ext
        new.entity_pool    = entity_pool
        new.entity_data._update_from_foreign_(request, f_entity_data)
        return new

    @classmethod
    def _init_from_connection_(cls, entity_pool, **connection_kwargs):
        new = cls()
        new.Is_Local_State = Entity_Ext
        new.entity_pool    = entity_pool
        new.entity_data.Connection._update_from_kwargs_(**connection_kwargs)
        return new
    
    @classmethod
    def _init_as_local_(cls, entity_pool=None):
        new = cls()
        new.Is_Local_State = Entity_Int
        if entity_pool:
            new.entity_pool    = entity_pool
        else:
            new.entity_pool    = new.Entity_Pool_Type()
        return new
    
    def Create_App(self):
        ''' Best recomended to start custom'''
        assert self.Is_Local_State is Entity_Int
        self._app = FastAPI()
        self._register(self._app,self.entity_pool)
        return self._app


