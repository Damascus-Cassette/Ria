from ....models.struct_file_io        import BaseModel
from ....statics                      import _unset
from ...utils.statics                 import get_data_uuid
from ..File_Utils                     import cache_folder, temp_folder
from ....base_modules.Execution_Types import _item,_mixin
from contextlib                      import contextmanager
from .Env_Variables import CACHE

from ....models.struct_hook_base import hook

from pydantic    import BaseModel as pydantic_Basemodel
from inspect     import isgeneratorfunction
from contextvars import ContextVar
from typing      import Any, Self
from enum        import Enum

class cache_item_location_state(Enum):
    LOCAL_MEM   = 'LOCAL_MEM'  
    LOCAL_DISC  = 'LOCAL_DISC' 
    MANAGER     = 'MANAGER'    
    SIBLING     = 'SIBLING'    

class cache_item_local_state(Enum):
    AVALIABLE   = 'AVALIABLE'
    UNAVALIABLE = 'UNAVALIABLE'
    DEPRECIATED = 'DEPRECIATED'

class cache_item_manager_state(Enum):
    NOT_UPLOADED = 'NOT_UPLOADED'
    AVALIABLE    = 'AVALIABLE'
    UNAVALIABLE  = 'UNAVALIABLE'
    DEPRECIATED  = 'DEPRECIATED'
    #AVALIABLE_FOREIGN 

class Cache_Item_Reference(pydantic_Basemodel): 
    # Single data-type meant to be frequently synced. Good use case for pydantic instead of internal fileio.BaseModel
    # Referes to the state of a single cache item which may or may not be local

    cache_uuid    : str
    manager_state : cache_item_manager_state

    _loc_state  : cache_item_location_state # Relative information for current thread 
    _state      : cache_item_local_state    
    local_only  : bool

class Cache_Itenerary[Cache_Item_Reference](dict):
    ''' May make this a socket synced datastructure '''


class Cache_Item(BaseModel):
    ''' Loaded from disc, mem or manager->mem. 
    Contains data to apply to a node on cache retrieval. Allows extra data as a generic.
    `extra_data` best used for controlled validation inside a func before yielding/returning or handled inside of yield & post
    Usual best practice with yield is to always locally ascociate the `state_key` with a cache in the wrapper, 
        so an exec function itself should only run once w/a
    Ascociated files are relative to the root, which should have an equivilent key.
        Can I collide in form but not files? No, as the UID is generated after evaluating the folder key.
        All oibjects are quirried for filepath convertion, and it's up to each non-trival data type to convert in/out of roots
    '''

    _io_blacklist_ = ['local_root']
    data_uid    : str                       #UID of this data, post conversion

    out_sockets : dict[str, dict[str, Any]] #Socket name/index, then attributes that are intaken. 
    extra_data  : dict                      #Generic data to be handled by the node itself

    space_ids   : tuple[str] = tuple() #Data UUID Hash of root's contents. Pre-calculating UID, just keep as indices
    local_roots : dict = None          #Local-only path to folder containing cache. Converts child-data from space_id somewhere on import. 

    def __init__(self,):
        self.out_sockets = {}
        self.extra_data  = {}
        self.local_roots = {} #Local fp conversion

    def ascociate_dir(self,dir):
        self.local_roots[dir] = None

    def transform_cache(self,memo)->Self:
        ''' Converts all first level strings, 
        quiries all non-trival data types.
        Blindspot of dicts/lists?
        '''
        raise NotImplementedError('TODO')

    def set_uid(self,):
        ''' This should happen after cache-folder is uploaded and self is transformed '''
        assert not getattr(self.data_uid)
        key =  get_data_uuid(self.out_sockets)
        key =+ get_data_uuid(self.extra_data)
        key =+ self.space_id
        self.data_uid = key

    # def references(self,Cache):...

cache_future_asc_public = ContextVar('cache_future_asc_public', default = None)
cache_future_asc_local  = ContextVar('cache_future_asc_local', default = None)

cache_cache_folders     = ContextVar('cache_cache_folders', default = None)
cache_temp_folders      = ContextVar('cache_temp_folders',  default = None)

from .Env_Variables import CACHE

class Cache():
    ''' Shallow container for all cache_items, handles cache retrieval w/a
    Synced with manager. Has a search func for finding caches
    Holds temporary 
    '''

    itenerary    : Cache_Itenerary
    data         : dict[Cache_Item] #Converted in place at task completion?

    # data_folders : #How should I track this data, apart from just folder location? 

    # foreignized_iten : dict[str,   str] #Prev and post-keys, buffer for converting itenerary and data
    # foreignized_data : dict[Cache_Item] #Converted dict
    
    def __init__(self,):
        self.itenerary = Cache_Itenerary()
        self.caches    = {}

    # def sync_item():
    #     ''' sync item from the manager class '''

    def create_cache_asc(self, cache_item, public=tuple(), local=tuple()):
        #For now making all public,
        local_key = None
        for k,v in self.caches.items():
            if v is cache_item:
                local_key = k
        if not local_key:
            raise Exception('Local Key not found!')

        for key_asc in public:
            self.itenerary[key_asc] = local_key
        # for key_asc in local:
        #     self.itenerary[key_asc] = local_key

    @classmethod
    def create_wrapper(self,func):
        if isgeneratorfunction(func):
            return self.value_cache_gen_wrapper(func)
        return self.value_cache_reg_wrapper(func)

    @staticmethod
    def value_cache_reg_wrapper(func):
        ''' Wrapper for Single-Step-Execution Function. Self is Node 
    
        Runs when state_key does not pass muster for current, and when memo does not intake.
    
        currently goes through these phases:
            node executes -> uncached & local -> cached & local -> cached ascociated & local

        '''
        def wrapper(self,*args,**kwargs):
            
            state_key = self.state_key
            if not self.comp_or_exec_allow(state_key):
                return None
            
            t1 = cache_future_asc_public.set([])
            t2 = cache_future_asc_local .set([])

            t3 = cache_cache_folders.set([])
            t4 = cache_temp_folders .set([])

            self.asscociate_key(state_key)

            if (res:=self.cache_search_key(state_key)) is _unset:
                #execute if not in cache            
                res = func(self,*args,**kwargs)

            if isinstance(res,Cache_Item):
                cache_item = res
                res = self.intake_cache(cache_item)


            elif self.create_cache:
                cache_item = self.create_cache()
                CACHE.get().add_cache(state_key,cache_item)
            
            CACHE.get().create_cache_asc(cache_item,
                        public = cache_future_asc_public.get(), 
                        local  = cache_future_asc_local.get() )

            cache_future_asc_public.reset(t1)
            cache_future_asc_local .reset(t2)

            cache_cache_folders.reset(t3)
            cache_temp_folders .reset(t4)
            #TODO: Add to global lists

            return res

        return wrapper


    @staticmethod
    def value_cache_gen_wrapper(func):
        ''' Wrapper for generator-Execution Function.  Self is Node.
        `yield` in func will consider function complete with first `not (yield_res is _unset)`
            - This includes `return None` and `yield None`

        Runs when state_key does not pass muster for current, and when memo does not intake.

        '''
        def wrapper(self,*args,**kwargs):
            
            state_key = self.state_key
            if not self.comp_or_exec_allow(state_key):
                return None

            t1 = self.cache_future_asc_public.set([])
            t2 = self.cache_future_asc_local .set([])

            t3 = cache_cache_folders.set([])
            t4 = cache_temp_folders .set([])

            if (res:=self.cache_search_key(state_key)) is not _unset:
                self.intake_cache(res)
            else:
                #execute if not in cache            
                self.asscociate_key(state_key)
                gen = func(self,*args,**kwargs)

                for res in gen:
                    if res is _unset:
                        continue

                    if isinstance(res, Cache_Item):
                        cache_item = res
                        res = self.intake_cache(cache_item)
                        break

                    if self.create_cache:
                        cache_item = self.create_cache()
                        CACHE.get().add_cache(state_key,cache_item)
                    break
                if res is _unset:
                    raise Exception(f'A resulting value cannot be unset! {self.__module__}.{self.__name__} : {func}')
                
            CACHE.get().create_cache_asc(cache_item,
                                  public = cache_future_asc_public.get(), 
                                  local  = cache_future_asc_local.get() )

            cache_future_asc_public.reset(t1)
            cache_future_asc_local .reset(t2)
            
            #task.asscociate_folders() Perhaps
            cache_cache_folders.reset(t3)
            cache_temp_folders .reset(t4)
            #TODO: Add to global lists?

            return res

        return wrapper


    def search(self,key):
        if self.itenerary.get(key, None):
            key = self.itenerary[key]
        return self.caches.get(key,_unset)


    def add_cache(self,original_key, cache_item:Cache_Item):
        self.caches[original_key] = cache_item
        self.itenerary[original_key] = original_key

class Cache_IO():
    ''' Inherited method class on each node for ease of access to caching functionality '''
    
    def cache_search(self, *args, asc_key = True):
        ''' Search itenerary of current cache object with UUIDs of argument inputs '''
        key = ''
        for x in args:
            key = key + get_data_uuid(key)
        return self.cache_search_key(key, asc_key = asc_key)
    
    def cache_search_key(self, key:str, asc_key = True):
        assert isinstance(key, str)
        cache : Cache = CACHE.get()
        if asc_key: self.asscociate_key(key)
        return cache.search(key)
        
    def asscociate_key(self, key:str, local_only=False):
        ''' Ascociates key with potential future cache '''
        assert isinstance(key, str)
        cache_future_asc_local.get().append(key)
        if not local_only:
            cache_future_asc_public.get().append(key)
        return _unset

    def intake_cache(self,):
        ''' Apply cache to current datastructure '''
        raise NotImplementedError('MUST BE IMPLIMENTED PER DATASTRUCTURE')

    def create_cache(self,):
        ''' Create cache from current datastructure '''
        raise NotImplementedError('MUST BE IMPLIMENTED PER DATASTRUCTURE')

    @contextmanager
    def cache_folder(self, *args,**kwargs):
        with cache_folder(self.state_key, *args,**kwargs) as cwd:
            global cache_cache_folders
            cache_cache_folders.get().append(cwd)
            yield cwd

    @contextmanager
    def temp_folder(self,*args,**kwargs):
        with temp_folder(self.state_key,*args,**kwargs) as cwd:
            global cache_temp_folders
            cache_temp_folders.get().append(cwd)
            yield cwd

class socket_mixin(_mixin.socket):
    def import_cache_data(self, data:dict)->None:
        self.value = data['value']
        
    def export_cache_data(self)->dict:
        data = {}
        data['value'] = self.value
        return data

class socket_collection_mixin(_mixin.socket_collection):
    def import_cache_data(self,data):
        for k,v in data.items():
            self[k].import_cache_data(v)
        
    def export_cache_data(self):
        data = {}
        for k,v in self.items():
            data[k] = v.export_cache_data()
        return data
        

class node_mixin(Cache_IO,_mixin.node): 
    
    @hook(event = 'compile', mode = 'wrap', key = '_compile_cache_wrap_')
    def _compile_cache_wrap_(self,func,*args,**kwargs):
        return Cache.create_wrapper(func)
    
    @hook(event = 'execute', mode = 'wrap', key = '_execute_cache_wrap_')
    def _execute_cache_wrap_(self,func,*args,**kwargs):
        return Cache.create_wrapper(func)

    def intake_cache(self,cache_item:Cache_Item):
        ''' Apply cache to current datastructure '''
        return self.out_sockets.import_cache_data(cache_item.out_sockets)

    def create_cache(self,):
        ''' Create cache from current datastructure '''        
        cache_item = Cache_Item()
        cache_item.out_sockets = self.out_sockets.export_cache_data()
        return cache_item
    
    def comp_or_exec_allow(self,state_key):
        ''' Allow cached execution/compilation to occur, 
        if nodes state already houses result of state key/similar this should return False '''
        return not (state_key in self.out_sockets[0]._value.keys())
        # return True
        ...
    

_cache_mixins_ = [
    socket_mixin,
    socket_collection_mixin,
    node_mixin,
]
_cache_items_  = []
_cache_tests_  = []