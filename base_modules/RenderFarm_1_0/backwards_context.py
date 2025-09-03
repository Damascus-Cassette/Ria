from ...statics  import _unset

from contextlib  import contextmanager
from contextvars import ContextVar
from typing      import Any


class BackwardsContextType(dict):    
    ''' May convert to a collection to allow better export & typed import via regular fileio '''

    def _export_(self,)->dict:
        # Export current key values w/a (not _unset) 
        #  & call basemodel export & import on them w/a (must be typed context??)
        ... 

    def __init__(self):
        super().__init__()
        self['_chain'] = tuple()

    def __missing__(self,k):
        self[k] = r = ContextVar('k', default = _unset)

    def set(self,key_or_values:dict|str, value:Any = _unset)->dict|Any:
        if isinstance(key_or_values,str):
            assert not (value is _unset)
            return res[key_or_values].set(value)

        res = {}
        for k,v in key_or_values.items():
            res[k] = self[k].set(v)

        return res
    
    def get(self, keys:dict|tuple|str)->dict|tuple|Any:
        if isinstance(keys,str):
            return self[keys].get()
        elif isinstance(keys,dict):
            res = {}
            for k,v in keys.items():
                res[k] = self[k].get()
        else:
            res = []
            for k in keys:
                res.append(self[k].get())
            return tuple(res)

    def reset(self,tokens:dict):
        for k,t in tokens.items():
            self[k].reset(t)

    @contextmanager
    def checkin(self, ident):
        t = self.set('_chain', self.get('_chain') + (ident,))
        yield
        self.reset()

    @contextmanager
    def values_as(self,values:dict):
        ret = {}
        for k, v in values.items():
            ret[k] = self[k].set(v)
        yield
        for k, t in ret.items():
            self[k].reset(t)
