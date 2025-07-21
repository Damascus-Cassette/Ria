
from typing import Callable, Any
#Generic collection


class item_base():
    key   : str
    label : str

class collection_base[T=item_base]():
    #### Constructed Values ####
    Base : T

    #### Instance Values ####
    data : list[T]
    
    @property
    def _data(self):
        ret = {}
        for x in self.data:
            ret[x.key] = x
        return ret
    
    def new(self,key,label,/,*,args,kwargs):
        assert key not in self._data.keys()
        inst = self.Base()
        inst.label = label
        inst.key   = key
        self.data.append(inst)
        return inst

    def set(self,key,item):
        self[key] = item

    def clear(self):
        for k in self._data.keys():
            self.remove(self,k)

    def remove(self,key):        
        item = self._data[key]
        self.data.remove(item)

    def __getitem__(self,k):
        return self._data[k]

    def __setitem__(self,k,item):
        assert isinstance(k,self.Base)
        item.key = k
        self.data.append(item)

    def values(self): 
        return self._data.values()

    def items(self):  
        return self._data.items()

    def keys(self):   
        return self._data.keys()
    
    def __init__(self):
        self.data = []

class collection_typed_base(collection_base):
    ''' Collection of multiple allowable types '''

    #### Constructed Values ####
    Bases : dict[str,Any]
    
    def new(self, type:str|Any, key, label,
            /,*,args:list=None,kwargs:dict=None):
        if args   is None: args   = []
        if kwargs is None: kwargs = {}

        if isinstance(type,str): assert type in self.Bases.keys()
        else:                    assert type in self.Bases.values()

        assert key not in self._data.keys()

        inst = self.Bases[type](*args,**kwargs)
        inst.label = label
        inst.key   = key

        self.data.append(inst)
        
        return inst
    
    def __setitem__(self,k,item):
        assert isinstance(k,[x for x in self.Base.values()])
        item.key = k
        self.data.append(item)
