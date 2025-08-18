from contextvars import ContextVar
from contextlib  import contextmanager
from typing      import Any
from types       import FunctionType

from ..statics   import _unset

class _defaultdict(dict):
    def __missing__(self, key):
        res = self[key] = ContextVar(key, default=False)
        return res

    @contextmanager
    def in_context(self,kwargs):
        ''' Utility function to add a dict as context '''
        _t = {}
        for k,v in kwargs.items():
            _t[k] = self[k].set(v)
        yield
        for k,t in _t.items():
            self[k].reset(t)



_context      = _defaultdict()
context_flags = _defaultdict()

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
    def Cached(self):
        _c_temp = {}
        with _context.in_context(self._Global_Context_Copy):
            with self.register():
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

    def Repr(self,chain=None,key_limiter:str=None):
        if chain is None: chain = []
        assert self not in chain
        chain.append(self)

        if (func:=getattr(self._parent,'_context_repr_',None)) is not None:
            return func(chain=chain)

        if len(self._Include) == 0:
            return getattr(self._parent,'_context_item_rootrep_','(CONTEXT_CHAIN_ERROR)')
        
        if self._Include[-1] is key_limiter:
            return f'({key_limiter})'

        if (pparent := getattr(self,self._Include[-1], None)) is not None:
            if (val:=getattr(self._parent,'_context_item_keyrep_',None)) is not None:
                return pparent.context.Repr(chain=chain,key_limiter=key_limiter) + val
            
            reversed_attr = {v:k for k,v in vars(pparent).items() if v is self._parent}
                #TODO: FUGLY FIX
            if self._parent in reversed_attr.keys(): 
                return pparent.context.Repr(chain=chain,key_limiter=key_limiter) + '.' + reversed_attr[self._parent]
            
            print('IN CONTEXT REPR:',getattr(self._parent,'_context_item_keyrep_',None))
                
        return getattr(self._parent,'_context_attr_fallback_',str(self._parent))
    
    def Formatted_Repr(self):
        return f'<Obj {self._parent.__class__} @ {self.Repr()} >'
    

    def __deepcopy__(self,memo:dict):
        ''' Ensure that deepcopy doesn't investigate parent chain. 
        Structurally all parent references *should* go through context '''
        if id(self._parent) not in memo.keys():
            raise Exception('Context cannot be deepcopied directly!')
        new_parent = memo[id(self._parent)]
        result = context(new_parent)
        memo[id(self)] = result
        return result
    
    @contextmanager
    def As_Env(self,**kwargs):
        ''' Utility retrieves self-cached env and allows setting of flags 
        Recomended to add wrapper function onto housing class for specifying and limiting flags
        '''
        with self.Cached():
            with context_flags.in_context(kwargs):
                yield
    


    
# class context_container_mixin():
#     context        : context
#     _context_walk_ : FunctionType

#     def __init_subclass__(cls):
#         assert hasattr(cls,'_context_walk_')

#     def __repr__(self,kick=False):
#         if (c:=getattr(self,'context',None)) is not None:
#             return c.Formatted_Repr()
#         else:
#             return super().__repr__
# Deemed to not be worth the hasle of mixing in, 