from ...models.struct_file_io import BaseModel
from ...statics               import _unset

from pydantic    import BaseModel as pydantic_Basemodel
from inspect     import isgeneratorfunction
from contextvars import ContextVar
from typing      import Any
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
    ''' May make this a synced datastructure '''


class Cache_Item(BaseModel):
    ''' Loaded from disc, mem or manager->mem. 
    Contains data to apply to a node on cache retrieval. Allows extra data as a generic.
    `extra_data` best used for controlled validation inside a func before yielding/returning or handled inside of yield & post
    Usual best practice with yield is to always locally ascociate the `state_key` with a cache in the wrapper, 
        so an exec function itself should only run once w/a
    '''

    data_uid    : str                       #UID of this data 

    out_sockets : dict[str, dict[str, Any]] #Socket name/index, then attributes that are intaken. 
    extra_data  : dict                      #Generic data to be handled by the node itself

    def __init__(self,):
        self.out_sockets = {}
        self.extra_data  = {}

    def set_uid(self,):
        assert not getattr(self.data_uid)
        key =  uuid_hash_from_data(self.out_sockets)
        key =+ uuid_hash_from_data(self.extra_data)
        self.data_uid = key

    # def references(self,Cache):...

current_cache           = ContextVar('current_cache', default = None) 
cache_future_asc_public = ContextVar('cache_future_asc_public', default = None)
cache_future_asc_local  = ContextVar('cache_future_asc_local', default = None)

class Cache():
    ''' Shallow container for all cache_items, handles cache retrieval w/a
    Synced with manager. Has a search func.
    '''

    itenerary : Cache_Itenerary
    data      : dict[Cache_Item]
    
    def __init__(self,):
        self.itenerary = Cache_Itenerary()
        self.caches    = {}

    # def sync_item():
    #     ''' sync item from the manager class '''


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
            if self.still_need_to_execute_or_cache(state_key):
                return None
            
            global cache_future_asc_public
            global cache_future_asc_local
            t1 = cache_future_asc_public.set([])
            t2 = cache_future_asc_local .set([])



            self.asscociate_key(state_key)

            if (res:=self.find_cache(state_key)) is _unset:
                #execute if not in cache            
                res = func(*args,**kwargs)

            if isinstance(res,Cache_Item):
                cache_item = res
                res = self.intake_cache(cache_item)


            elif self.create_cache:
                cache_item = self.create_cache()
                global current_cache
                current_cache.get().add_cache(cache_item)
            
            self.create_cache_asc(cache_item)

            cache_future_asc_public.reset(t1)
            cache_future_asc_local .reset(t2)

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
            self:node
            
            state_key = self.state_key
            if self.still_need_to_execute_or_cache(state_key):
                return None

            global cache_future_asc_public
            global cache_future_asc_local
            t1 = self.cache_future_asc_public.set([])
            t2 = self.cache_future_asc_local .set([])

            if (res:=self.find_cache(state_key)) is not _unset:
                self.intake_cache(res)
            else:
                #execute if not in cache            
                self.asscociate_key(state_key)
                gen = func(*args,**kwargs)

                for res in gen:
                    if res is _unset:
                        continue

                    if isinstance(res, Cache_Item):
                        cache_item = res
                        res = self.intake_cache(cache_item)
                        break

                    if self.create_cache:
                        cache_item = self.create_cache()
                        global current_cache
                        current_cache.get().add_cache(cache_item)
                    break
                if res is _unset:
                    raise Exception(f'A resulting value cannot be unset! {self.__module__}.{self.__name__} : {func}')
                
            self.create_cache_asc(cache_item)

            cache_future_asc_public.reset(t1)
            cache_future_asc_local .reset(t2)

            return res

        return wrapper

class Cache_IO():
    ''' Inherited method class on each node for ease of access to caching functionality '''
    
    def cache_search(self,):        
        ...

    def intake_cache():
        ...

    def add_cache():
        ...

    def asscociate_key(self,key:str):
        ''' Ascociates key with potential future cache '''
        ...

class node_mixin(Cache_IO,_mixin.node): ...

_cache_mixins_ = [
    node_mixin
]
_cache_items_  = []
_cache_tests_  = []