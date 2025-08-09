''' Collection base classes to mixin to other classes & Format
Subtypes should be able to Merge left when Mergable_Base = True
'''


from .struct_merge_tools import merge_wrapper
from .struct_context     import context
# from .struct_file_io import BaseModel
    #Want to keep each struct module as seperate as possible.

from collections import OrderedDict
from typing      import Self,Callable,Type
from types       import FunctionType


class item_base():
    key   : str
    label : str

class collection_base[T=item_base]():
    ''' OrdereDict wrapper that allows typing via bases prop or func '''

    #### Constructed Values #### 
    Base           : Type
    Merge_By_Keys  : bool = False   #Can merge by keys (merge left w/a with merge_bases) or make keys unique
    Mergeable_Base : bool = False   
        #Subtypes should allow merging when this is true
        #If this is not True, it will replace like a dict and not deep replace-refs

    Allow_Unique_Generation : bool = True

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
            with self.context.In_Last_Context():
                func()

    def ensure_unique_key(self,key):
        if key not in self._data.keys():
            return key
        elif not self.Allow_Unique_Generation:
            raise Exception('KEY NOT UNIQUE WHILE CLASS DEMANDS UNIQUE')
        
        key_base = key
        i = 0
        while key in self._data.keys():
            if i > 999: raise Exception('WHAT ARE YOU DOING???')
            i   =+ 1
            key = key_base + '.' + str(i).zfill(3)
        
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

    def __setitem__(self,key,item):
        ''' Replace key if mergable or generate new key and move'''
        assert self.matches_base(item)
        
        if key in self._data.keys():
            if self.Mergeable_Base and self.Merge_By_Keys:
                item = item | self._data[key]
                # self._context_new_item_(item)

            elif not self.Merge_By_Keys:
                key = self.ensure_unique_key(key)

        item.key = key
            #FUGLY AND NOT IDEAL AT ALL
            #May tie back collection -> child via child.in_collections 
            # or similar reflection, require key as a get and have repr choose the first collection.

        self._data[key] = item
        self._context_new_item_(item)

    def __setmerge__(self,key,item):
        ''' add/merge local w/a or discard incoming '''
        assert self.matches_base(item)
        
        if key in self._data.keys():
            if self.Mergeable_Base:
                item = item | self._data[key]
                self._context_new_item_(item)
                self._data[key] = item
                return item
            # Do not merge otherwise. 
            # TODO have to add to memo for merge that one was chosen over another
        
        else:
            self._data[key]=item

    def __getitem__(self,key:str|int):
        if isinstance(key,int):
            return list(self.data.items())[key][1]
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

    def matches_base(self,item):
        return isinstance(item,self.Base)

    @merge_wrapper
    def __or__(self, other:Self|OrderedDict):
        ''' Merge via set_item, merge left. Maintain filter & Order'''
        assert other.__class__ is self.__class__
        
        for i,k,v in other:
            self.__setmerge__(k,v)

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
    
    def new(self, *args, suppress_filter_check = False,**kwargs,)->T:
        '''In a subcollection an item'''
        inst = super().new(*args,**kwargs)
    
        if not suppress_filter_check:
            assert self._filter(inst)
        return inst

    @merge_wrapper
    def __or__(self,other:Self):
        ''' Union, merge filters & cover gaps in parent's collection, merging filters may unwanted additional coverage '''
        ''' Merge left '''
        assert other.__class__ is self.__class__
        
        self._filter = lambda i,k,v : other._filter(v) or self._filter(v)
        
        for i,k,v in other.iter():
            self.__setmerge__(k,v)


class typed_collection_base[T](collection_base):
    
    Bases : dict[str,Type]

    def matches_base(self, item:str|Type):
        Bases = getattr(self,'Bases',{})

        if isinstance(item,str):
            return item in Bases.keys()
        else:
            return item.__class__ in Bases.values()
        
    
    def new(self, type:str|Type, key, label=None, *args,**kwargs):
        Bases = getattr(self,'Bases',{})
        assert self.matches_base(type)
        
        if label is None: label = key

        if isinstance(type,str): 
            type : Type = Bases[type]

        with self.context.In_Last_Context():
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