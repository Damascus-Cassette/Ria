''' TODO: re-write this module to simplify structure of a collection w/ subcollections in mind'''


from typing import Callable, Any
#Generic collection

from .struct_context import context
from contextlib import contextmanager

class item_base():
    key   : str
    label : str

class collection_base[T=item_base]():
    #### Constructed Values ####
    Base : T

    #### Instance Values ####
    data : list[T]
    
    context = context.construct()
    def _context_walk_(self):
        with self.context.register():
            for x in self.data:
                if func:=getattr(x,'_context_walk_',None):
                    func()
    def _context_new_item_(self,item):
        if func:=getattr(item,'_context_walk_',None):
            with self.context.In_Last_Context():
                func()            

    @property
    def _data(self):
        ret = {}
        for x in self.data:
            ret[x.key] = x
        return ret
    
    def new(self,key,label=None,*args,**kwargs):
        assert key not in self._data.keys()
        if label is None: label = key
        inst = self.Base(*args,**kwargs)
        inst.label = label
        inst.key   = key
        self.data.append(inst)
        self._context_new_item_(inst)
        return inst

    def set(self,key,item):
        self._context_new_item_(item)
        self[key] = item

    def clear(self):
        for k in self._data.keys():
            self.remove(self,k)

    def remove(self,key):        
        item = self._data[key]
        self.data.remove(item)

    def __getitem__(self,k):
        if isinstance(k,int):
            return self.data[k]
        return self._data[k]

    def __setitem__(self,k,item):
        assert isinstance(k,self.Base)
        item.key = k
        self.data.append(item)
        self._context_new_item_(item)

    def values(self): 
        return self._data.values()

    def items(self):  
        return self._data.items()

    def keys(self):   
        return self._data.keys()
    
    def __init__(self):
        self.context = self.context(self)
        self.data = []

    def __iter__(self):
        for v in self.values():
            yield v

    def __len__(self):
        return len(self.values())

    # def _UKey_Generator(self,item,key:str):
    #     ''' Verify ID is Unique before attaching, '''
    #     key_base = getattr(item,'key',key)
    #     key = key_base
    #     i = 0
    #     while key in self.keys():
    #         i=+1
    #         key = key_base + '.' + str(i).zfill(3)
    #     return key

class collection_typed_base[T](collection_base):
    ''' Collection of multiple allowable types '''

    #### Constructed Values ####
    Bases : dict[str,Any]
        #Replaced in inherited to be filtered property of root_graph.
    
    def new(self, type:str|Any, key, label=None,*args,**kwargs):
        Bases = self.Bases
        if label is None: label = key

        if isinstance(type,str): assert type in Bases.keys()
        else:                    assert type in Bases.values()

        assert key not in self._data.keys()

        with self.context.In_Last_Context():
            inst = Bases[type](*args,**kwargs)
        inst.label = label
        inst.key   = key

        self.data.append(inst)

        # self._context_new_item_(inst)
        
        return inst

    
    def __setitem__(self,k,item):
        x = tuple(self.Bases.values())
        assert isinstance(item,x)
        item.key = k
        self.data.append(item)
        self._context_new_item_(item)

from collections import OrderedDict

class subcollection[T](collection_base):
    ''' A collection initlizied with another collection's data and containing a lambda filter. '''
    #TODO: SCUFFED, Rewrite entire module
    
    def __init__(self, base_collection:collection_base, filter_func:Callable):
        self.data   = base_collection
        self.filter     = filter_func

    data : collection_base

    def __iter__(self):
        for v in self.data:
            if self.filter(v):
                yield v

    @property
    def _data(self)->dict:
        return OrderedDict({x.key:x for x in self})
        
    def __getitem__(self,key:str|int)->T|None:
        return self.data[key]

    def __setitem__(self, k, item):
        self._data[k] = item
    
    def new(self, key, label=None, *args, **kwargs):
        item = self._data.new(key, label, *args, **kwargs)


class typed_subcollection[T](subcollection,collection_typed_base):
    ...