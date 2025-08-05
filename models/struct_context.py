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
    _Global_Context_Copy : dict[str, Any]
    _Include : list[str]
    _As_Name : str|None  = None
    _Constructed : bool  = False

    @classmethod
    def construct(cls, include:list[str]=None, as_name:str|None = None):
        ''' construct context object to initialize with self, 
        Constext object must be constructed'''
        if include is None:
            include = []
        kwargs = {'_Include': include,
                  '_As_Name': as_name,
                  '_Constructed':True}
        return type('Context',(cls,),kwargs)


    #### Instance Values ####
    _parent  : Any

    def __init__(self,parent):
        assert self._Constructed

        self._Global_Context_Copy = {}
        self._parent = parent
        self._Get()

    def _Get(self):
        for k in self._Include:
            val = _context[k].get()
            setattr(self,k,val)

    def _Copy(self):
        self._Global_Context_Copy = {}
        for k,v in _context.items():
            if not ((_v :=v.get()) is None):
                self._Global_Context_Copy[k] = _v
    
    @contextmanager
    def In_Last_Context(self):
        _c_temp = {}
        for k,v in self._Global_Context_Copy.items():
            _c_temp[k]=_context[k].set(v)
        with self.register():
            yield
        for k,v in _c_temp.items():
            _context[k].reset(_c_temp[k])
    
    @contextmanager
    def Cached(self):
        with self.In_Last_Context():
            yield

    @contextmanager
    def register(self):
        self._Copy()
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