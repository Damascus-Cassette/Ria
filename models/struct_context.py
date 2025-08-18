from contextvars import ContextVar
from contextlib  import contextmanager
from typing      import Any
from types       import FunctionType

from ..statics   import _unset

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

    # def __repr__(self):
    #     res = ' '.join([f' | {x} : {getattr(self,x,_unset)} ' for x in self._Include])
    #     res = f'<Context object of chain: {res}>'
    def KeyRep(self,key:str):
        ''' Rep with fallback for structures still initializing '''
        if not (a := getattr(self,key,None)):
            return f'(Context["{key}"])'
        else:
            a.__repr__().split('@')[-1].strip('<>')

    def Repr(self,chain=None):
        if chain is None: chain = []
        assert self not in chain
        chain.append(self)

        if (func:=getattr(self._parent,'_context_repr_',None)) is not None:
            return func(chain=chain)
        
        elif (pparent := getattr(self,self._Include[-1], None)) is not None:
            reversed_attr = {v:k for k,v in vars(pparent).items() if v is self._parent}
                #TODO: FUGLY FIX
            if self._parent in reversed_attr.keys(): 
                return pparent.context.Repr(chain=chain) + '.' + reversed_attr[self._parent]
            elif (val:=getattr(self._parent,'_context_item_keyrep_',None)) is not None:
                return pparent.context.Repr(chain=chain) + '.' + val
                
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