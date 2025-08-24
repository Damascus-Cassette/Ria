''' Collection base classes to mixin to other classes & Format
Subtypes should be able to Merge left when Mergable_Base = True
'''


# from .struct_merge_tools import merge_wrapper
from .struct_context   import context,_context, context_flags
from .struct_hook_base import hook_trigger, Hookable

from collections         import OrderedDict
from typing              import Self,Type,Any
from types               import FunctionType
from copy                import deepcopy,copy



class item_base():
    key   : str
    label : str

    @property
    def _context_item_keyrep_(self):
        return f"['{self.key}']"
    def _collection_item_auto_add_(self,add_to:str,flag:str|bool):
        ''' Auto append to context[add_to] if context_flags[flag] '''
        if not (p_col:=_context[add_to].get()) is False:
            if self not in p_col.values() and ((flag is True) or context_flags[flag].get()):
                p_col[getattr(self,'Label',getattr(self,'UID',self.__class__.__name__))] = self

class collection_base[T=item_base]():
    ''' OrdereDict wrapper that allows typing via bases prop or func '''

    #### Constructed Values #### 
    Base           : Type
    _coll_generate_unique_keys_ : bool = True

    _coll_merge_on_setitem_ : bool = False   #Can merge by keys (merge left w/a with merge_bases) or make keys unique
    _coll_mergeable_base_   : bool = False
        #Subtypes should allow merging when this is true
        #If this is not True, it will replace like a dict and not deep replace-refs
    def _coll_merge_handler_(self,left,right):
        return left | right

    #### Instance ####
    _data   : OrderedDict  = None
    _order  : FunctionType    = lambda s,ikv: ikv[0]

    context = context.construct()
    def _context_walk_(self):
        with self.context.register():
            for x in self.data.values():
                if func:=getattr(x,'_context_walk_',None):
                    func()
    def _context_new_item_(self,item):
        if func:=getattr(item,'_context_walk_',None):
            with self.context.Cached():
                func()

    def ensure_unique_key(self,key):
        if key not in self._data.keys():
            return key
        elif not self._coll_generate_unique_keys_:
            raise Exception('KEY NOT UNIQUE WHILE CLASS DEMANDS UNIQUE')
        return self.make_unique_key(key)
    
    def make_unique_key(self,key)->str:
        key_base = key
        i = 0
        while key in self._data.keys():
            if i > 999: raise Exception('WHAT ARE YOU DOING???')
            i   =+ 1
            key = key_base + '.' + str(i).zfill(3)
        # print (f'MAKING KEY UNIQUE {key_base} TO {key}')
        return key

    @property
    def data(self)->OrderedDict:
        ''' filtered data '''
        values = sorted([(i,k,v) for i,(k,v) in enumerate(self._data.items())],key = self._order)
        res    = OrderedDict({k:v for i,k,v in values})
        return res

    def __init__(self):
        self.context = self.context(self)
        self._data   = OrderedDict()

    @hook_trigger(event = 'new_item')
    def new(self,key,label=None,*args,**kwargs):
        key = self.ensure_unique_key(key)
        if label is None: label = key
        inst       = self.Base(*args,**kwargs)
        
        inst.label = label
        inst.key   = key
            #FUGLY, see note below

        self._data[key] = inst
        self._context_new_item_(inst)
        return inst

    @hook_trigger(event = '__setitem__')
    def __setitem__(self,key,item):
        ''' Replace key if mergable or generate new key and move'''
        assert self.item_verify_compatable(item)
        
        if key in self._data.keys():
            if self._coll_mergeable_base_ and self._coll_merge_on_setitem_:
                item = self._coll_merge_handler_(item, self._data[key])
                # self._context_new_item_(item)

            elif not self._coll_merge_on_setitem_:
                key = self.ensure_unique_key(key)

        item.key = key
            #FUGLY AND NOT IDEAL AT ALL
            #May tie back collection -> child via child.in_collections 
            # or similar reflection, require key as a get and have repr choose the first collection.

        self._data[key] = item
        self._context_new_item_(item)

        return item

    def __setmerge__(self,key,item):
        ''' add/merge local w/a or discard incoming '''
        assert self.item_verify_compatable(item)
        
        if key in self._data.keys():
            if self._coll_mergeable_base_:
                item = self._coll_merge_handler_(item, self._data[key]) 
                self._context_new_item_(item)
                self._data[key] = item
                return item
            # Do not merge otherwise. 
            # TODO have to add to memo for merge that one was chosen over another
        
        else:
            self._data[key]=item

    def __getitem__(self,key:str|int):
        if isinstance(key,int):
            return list(self.data.values())[key]
            # return list(self.data.items())[key][1]
        return self.data[key]

    def __len__(self):
        return len(self.data)
    
    def __iter__(self):
        for v in self.data.values():
            yield v
    
    def iter(self):
        for i,(k,v) in enumerate(self.data.items()):
            yield i,k,v
        
    def items(self):
        for k,v in self.data.items():
            yield k,v
    def keys(self):
        for k in self.data.keys():
            yield k
    def values(self):
        for v in self.data.values():
            yield v

    def item_verify_compatable(self,item):
        return isinstance(item,self.Base)

    # @merge_wrapper
    def __or__(self, other:Self|OrderedDict):
        ''' Merge via set_item, merge left. Maintain filter & Order'''
        assert other.__class__ is self.__class__
        
        for i,k,v in other:
            self.__setmerge__(k,v)

    def item_verify_local(self,item)->bool:
        return item in self.values()
    
    def free(self,item:T, safe=True)->T:                            
        ''' Free Item, ie 'pop' from this collection. 
        safe: that an error will be thrown if not in collection's local data  '''
        if self.item_verify_local(item): self.data.popitem(item)
        elif safe: raise Exception('Non-Local Object!')
        return item
    def free_multi(self,items:slice|tuple[T], safe=True)->tuple[T]:        
        ''' Free Item, ie 'pop' all in tuple this collection multi. 
        safe: an error will be thrown if not in collection's data '''
        if isinstance(items,slice): items = self[items]
        res = []
        for x in items:
            res.append(self.free(x,safe=safe))
        return tuple(res)

    def copy(self,item, safe=True, keep=True,return_memo=False,memo=None)->T:                              
        ''' deepcopy item and return the copy. 
        keep : 'append' the copy to this collection. (Ensures key name is unique if kept)
        safe : an error will be thrown if not in collection's data 
        return_memo : the memo used in deepcopy will be returned
        memo        : optional pass in a memo to use in the deepcopy
        '''
        
        if safe: assert self.item_verify_local(item)
        if memo is None : memo = {}
        memo = copy(memo)
        new = deepcopy(item,memo=memo)
        if keep: self[self.make_unique_key(new.key)] = new
        if return_memo: return new,memo 
        return new
    
    def copy_multi(self,items:slice|tuple[T],safe=True,keep=True,return_memo=False,memo=None)->tuple[T]:        
        ''' deepcopy items and return the copy. 
        memo is shared accross all deepcopy calls
        keep        : 'extend' the copies to this collection (Ensures key name is unique if kept)
        safe        : an error will be thrown if not in collection's data,
        return_memo : the memo used in deepcopy will be returned
        memo        : optional pass in a memo to use in the deepcopy
        '''
        if memo is None : memo = {}
        memo = copy(memo)
        if isinstance(items,slice): items = self[items]
        res = []
        for item in items:
            new,memo = self.copy(item,safe=safe,keep=keep,return_memo=True,memo=memo)
            res.append(new)
        if return_memo:
            return tuple(res), memo
        return tuple(res)

    def copy_in(self, item,col2:Self=None, local_copy=False,return_memo=False,memo=None):
        ''' Copy item from secondary collection. Must be compatable with self.base(s)
        local_copy  : use this collection's copy method 
        return_memo : the memo used in deepcopy will be returned
        memo        : optional pass in a memo to use in the deepcopy
        '''
        assert self.item_verify_compatable(item)
        if memo is None : memo = {}
        memo = copy(memo)
        if local_copy: return self.copy(item,safe=False,keep=True ,return_memo=return_memo, memo=memo)
        else:          return col2.copy(item,safe=True ,keep=False,return_memo=return_memo, memo=memo)

    def copy_in_multi(self,items:slice|tuple[T], col2:Self=None, local_copy=False, return_memo=False,memo=None,filter=None):
        ''' Copy items from secondary collection, 
        memo is shared accross all deepcopy calls
        local_copy  : use this collection's copy method, if false must provide col2 
        return_memo : the memo used in deepcopy will be returned
        memo        : optional pass in a memo to use in the deepcopy
        '''
        if isinstance(items,slice): items = self[items]
        if memo is None : memo = {}
        memo = copy(memo)
        res  = []
        for item in items:
            if not filter(item): continue
            item,memo = self.copy_in(item,col2,local_copy=local_copy,return_memo=True,memo=memo)
            res.append(item)
        if return_memo: return res,memo
        return res 


class subcollection_base[T](collection_base):
    # @property
    # def _io_write_(self): return self._data.__class__ != collection_base
    
    _io_write_ : bool            = False
    _data      : collection_base 
    _filter    : FunctionType    = lambda i,k,v: True
    _order     : FunctionType    = lambda s,ikv: ikv[0]

    def __init__(self, parent:collection_base, _filter:FunctionType=None):
        self._data   = parent
        self._filter = _filter
    
    @property
    def data(self)->OrderedDict[str,T]:
        ''' filtered data '''
        values = sorted([(i,k,v) for i,(k,v) in enumerate(self._data.items()) if self._filter(i,k,v)],key = self._order)
        res    = OrderedDict({k:v for i,k,v in values})
        return res
    @hook_trigger(event = 'new_item')
    def new(self, *args, suppress_filter_check = False,**kwargs,)->T:
        '''In a subcollection an item'''
        inst = super().new(*args,**kwargs)
    
        if not suppress_filter_check:
            assert self._filter(inst)
        return inst

    # @merge_wrapper
    def __or__(self,other:Self):
        ''' Union, merge filters & cover gaps in parent's collection, merging filters may unwanted additional coverage '''
        ''' Merge left '''
        assert other.__class__ is self.__class__
        
        self._filter = lambda i,k,v : other._filter(v) or self._filter(v)
        
        for i,k,v in other.iter():
            self.__setmerge__(k,v)


class typed_collection_base[T](collection_base):
    
    Bases : dict[str,Type]

    def item_verify_compatable(self, item:str|Type):
        Bases = getattr(self,'Bases',{})

        if isinstance(item,str):
            return item in Bases.keys()
        else:
            return item.__class__ in Bases.values()
        
    @hook_trigger(event = 'new_item')
    def new(self, type:str|Type, key, label=None, *args,**kwargs):
        Bases = getattr(self,'Bases',{})
        assert self.item_verify_compatable(type)
        
        if label is None: label = key

        if isinstance(type,str): 
            type : Type = Bases[type]

        with self.context.Cached():
            inst = type(*args,**kwargs)
        
        inst.label = label
        inst.key   = key

        self[key]  = inst
        # self._context_new_item_(inst) #Ruyn within __setitem__ function
        return inst


class typed_subcollection_base[T](typed_collection_base):
    # @property
    # def _io_write_(self): return self._data.__class__ != collection_base
    
    _io_write_ : bool            = False
    _data      : collection_base 
    _filter    : FunctionType    = lambda i,k,v: True
    _order     : FunctionType    = lambda s,ikv: ikv[0]

    def __init__(self, parent:collection_base, _filter:FunctionType=None):
        self._data   = parent
        self._filter = _filter
    
    @property
    def data(self)->dict:
        ''' filtered data '''
        values = sorted([(i,k,v) for i,(k,v) in enumerate(self._data.items()) if self._filter(i,k,v)],key = self._order)
        res    = OrderedDict({k:v for i,k,v in values})
        return res
    @hook_trigger(event = 'new_item')
    def new(self, *args, suppress_filter_check = False,**kwargs,):
        '''In a subcollection an item'''
        inst = super().new(*args,**kwargs)
    
        if not suppress_filter_check:
            assert self._filter(inst)
        return inst

    def __or__(self,other:Self):
        ''' Union, merge filters & cover gaps in parent's collection, merging filters may unwanted additional coverage '''
        ''' Merge left '''
        assert other.__class__ is self.__class__
        
        self._filter = lambda i,k,v : other._filter(v) or self._filter(v)
        
        for i,k,v in other.iter():
            self.__setmerge__(k,v)


class context_prepped_subcollection_base(subcollection_base):
    parent : Any
    _data  : property

    def __init__(self,parent,filter):
        self.parent = parent
        if filter:
            self._filter = filter
    

class context_prepped_typed_subcollection_base(typed_subcollection_base):
    parent : Any
    _data  : property

    def __init__(self, parent:Any, filter:FunctionType=None):
        self.parent   = parent
        if filter:
            self._filter = filter
    