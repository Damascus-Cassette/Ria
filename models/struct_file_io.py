
# This re-write changes some terms

from typing import get_args, Any, Self, Callable
from types import UnionType
from contextlib  import contextmanager, ExitStack
from contextvars import ContextVar
from typing import Self, ForwardRef
from collections import OrderedDict,defaultdict

class _unset:...
class _defaultdict(dict):
    def __missing__(self,key):
        ret = self[key] = ContextVar('key', default=None)
        return ret

context : dict[ContextVar] = _defaultdict()

class defered_archtype:
    Types : list[Any]

    @classmethod
    def construct(cls,Name):
        return type(f'{Name}_defered', cls, {'Types':[]})
    
    def __init_subclass__(cls):
        cls.Types = []
    
    def __init__():
        raise Exception('defered_archtype is a container class, construct or inherit instead!')

def collapse_type_chain(ty)->list:
    res = []
    for x in ty:
        if x.__class__ is UnionType:
            for e in x.__args__:
                res.extend(collapse_type_chain(e))
        if issubclass(x,defered_archtype):
            for e in x.types:
                res.extend(collapse_type_chain(e))
        else:
            res.append(x)
    return res

class flat_bin[key,*bases]():
    ''' A context attached bin, iteravily exported on context exit. Each stored object must be in a collection '''

    Strict : bool = True

    defered_refs : list[Callable]
    data         : dict[str,Any]

    @classmethod
    def from_union(cls,union:UnionType,container):
        key  = union.__args__[0]
        types = union.__args__[1]

        if isinstance(key,ForwardRef):
            key = key.__forward_arg__
        else:
            key = getattr (key,'__flat_bin_key__',key.__name__)

        return cls(container = container, key = key, types = types)

    def __init__(self,*,container,key,types):
        self.container = container
        self.key   = key
        self.types = types
        self.data  = {}

    @contextmanager
    def enter_context(self, export = False):
        t = context[self.key].set(self)
        try:    yield
        except: raise
        finally: 
            if export:
                self.defered_resolve()
            else:
                del self.data
                self.data = {}
        context[self.key].reset(t)

    def defered_resolve(self):
        #iteravily export each item in self.data
        ... 

class flat_ref[base,key=_unset]():
    container : Any

    base_type : base
    key_value : str

    @classmethod
    def from_union(cls,union:UnionType,container):
        base = union.__args__[0]
        key  = union.__args__[1]

        if key is _unset:
            key = getattr (base,'__flat_bin_key__',base.__name__)
        elif isinstance(key,ForwardRef):
            key = key.__forward_arg__

        return cls(container = container,)
    
    def __init__(self,*,container,key,types)->base:
        ...

class flat_col[key=_unset,*bases]():
    ''' Treat value like a list or dict that returns binnable &  BaseModel compatable items to store in bin of key.
        Currently There is no use of types as the types should be enforced on, and compatable with the bin
        This may change to type check the contents
       '''

    @classmethod
    def from_union(cls,union,container):
        ...

    def __init__(self,*,container:Any,types:Any,key:str)->base:
        assert getattr(container,'_io_list_like_',False) or getattr(container,'_io_list_like_',False)
        self.container = container
        self.types = types
    
    @classmethod
    def from_union(cls,union:UnionType,container):
        key  = union.__args__[0]
        types = union.__args__[1]

        if isinstance(key,ForwardRef):
            key = key.__forward_arg__
        else:
            key = getattr (key,'__flat_bin_key__',key.__name__)

        return cls(container = container, key = key, types = types)



class BaseModel:
    __io_orig_fields__ : dict[str,str]

    __io_orig_bins__ : dict[str,flat_bin]
    __io_orig_cols__ : dict[str,flat_col]
    __io_orig_refs__ : dict[str,flat_ref]

    __io_bins__      : dict[str,flat_bin]
    __io_cols__      : dict[str,flat_col]
    __io_refs__      : dict[str,flat_ref]

    _io_list_like_   : bool
    _io_dict_like_   : bool

    _io_ducktyping_  : bool
    _io_whitelist_   : list[str]
    _io_blacklist_   : list[str]

    @classmethod
    def __io_fields__(cls,existing_inst=None):
        ''' Get fields using above attributes '''
        if existing_inst: cls = existing_inst
        
    @classmethod
    def _cls_import_(cls,data:list|dict,existing_inst=None,):
        if existing_inst:
            existing_inst._import_(data)
            return existing_inst
        else:
            inst = cls()
            inst._import_(data)
            return inst
        
    @classmethod
    def _cls_append_(cls,data,existing_inst=None):
        if not existing_inst:
            return cls._cls_import_(data)
        else:
            return existing_inst._append_(data)

    @classmethod
    def _cls_export_(cls,existing_inst=None):
        if not existing_inst:
            return _unset
        else:
            return existing_inst._export_()

    def __init_subclass__(cls):
        cls.__io_organize_types__()

    @classmethod
    def __io_organize_types__(cls):
        cls.__io_orig_bins__ = {}
        cls.__io_orig_cols__ = {}
        cls.__io_orig_refs__ = {}
        cls.__io_fields__ = {}
        #TODO: Set __orig_cols|refs|bins__
        
        for k,v in cls.__annotations__.items():
            if src := getattr(v,'__origin__',None):
                if   issubclass(src,flat_ref):
                    cls.__io_orig_refs__[k] = v
                elif issubclass(src,flat_col):
                    cls.__io_orig_cols__[k] = v
                elif issubclass(src,flat_bin):
                    cls.__io_orig_bins__[k] = v
            else:
                cls.__io_fields__[k] = v 

    def __io_attach_refs__(self):
        self.__io_refs__ = {}
        for k,v in self.__io_orig_refs__.items():
            self.__io_refs__[k] = v.__origin__.from_union(v,self)

    def __io_attach_cols__(self):
        self.__io_cols__ = {}
        for k,v in self.__io_orig_cols__.items():
            self.__io_cols__[k] = v.__origin__.from_union(v,self)

    def __io_attach_bins__(self):
        self.__io_bins__ = {}
        for k,v in self.__io_orig_bins__.items():
            self.__io_bins__[k] = v.__origin__.from_union(v,self)

    @contextmanager
    def __io_attach__(self):
        self.__io_attach_refs__()
        self.__io_attach_bins__()
        self.__io_attach_refs__()
        with ExitStack() as stack:
            for k,v in self.__io_refs__.items():
                stack.enter_context(v.enter_context)
            for k,v in self.__io_cols__.items():
                stack.enter_context(v.enter_context)
            for k,v in self.__io_bins__.items():
                stack.enter_context(v.enter_context)
            yield

    @contextmanager
    def _io_import_(self):
        with self.__io_attach__():
            yield
        
    @contextmanager
    def _io_export_(self):
        with self.__io_attach__():
            yield
        
    @contextmanager
    def _io_append_(self):
        with self.__io_attach__():
            yield


    def _export_(self):
        with self._io_export_():
            ...
    def _import_(self, data):
        with self._io_import_():
            ...
    def _append_(self, data):
        with self._io_append_():
            ...

if __name__ == '__main__':
    
    class item_archtype(defered_archtype):...

    class item():
        __flat_bin_key__ = 'item'
    
    class col(BaseModel):
        __io_list_like__ = True  
        __io_dict_like__ = False 
            #When true, use method as IO when loading & diffing on a pre-existing instance

        @classmethod
        def _cls_import_(cls,data):
            ''' If defined, use this to import data.
                Generally expects an instance to be returned 
                Can be used to construct and return type or pre-load data/change archtypes '''
            inst = cls()
            inst.super()._import_(data)
            return inst

    class root(BaseModel):
        __io_ducktyping__ = False
            #Attributes only on class vs any attributes

        __io_whitelist__ = ['item_col', 'doesnt_export']
        __io_blacklist__ = ['doesnt_export']
            #record all fields (gatherd post ducktyping) on start minus blacklist 



        item_bin : flat_bin['item',item_archtype] #all subtypes stored on disc here

        item_col : flat_col[col , 'item'] = None 
        item_ref : flat_ref[item, 'item'] = None
        item_ref : flat_ref[item]         = None

        doesnt_export : str = ''

    item_archtype.Types.append(item)