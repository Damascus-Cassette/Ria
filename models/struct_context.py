from contextvars import ContextVar
from contextlib  import contextmanager
from typing      import Any

class _defaultdict(dict):
    def __missing__(self, key):
        res = self[key] = ContextVar(key, default=None)
        return res

_context = _defaultdict()

class context():
    ''' Constructed class meant to store data to/from a global context through a walk 
        Convention is using a function called _context_walk_ on the parent
        Must be init on parent's init'''

    #### Constructed Values ####
    _Include : list[str]
    _As_Name : str|None  = None


    @classmethod
    def construct(cls, include:list[str]=None, as_name:str|None = None):
        kwargs = {'_Include':include if include else [],
                  '_As_Name':as_name}
        return type('Context',(cls,),kwargs)


    #### Instance Values ####
    _parent  : Any

    def __init__(self,parent):
        self._parent = parent
        self._Get()

    def _Get(self):
        for k in self._Include:
            val = _context[k].get()
            setattr(self,k,val)

    @contextmanager
    def register(self):
        self._Get()
        try:
            t = None
            if self._As_Name:
                t = _context[self._As_Name].set(self._parent)
            yield
        except:
            raise
        finally:
            if t:
                _context[self._As_Name].reset(t)