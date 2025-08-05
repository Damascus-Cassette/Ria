from typing import ForwardRef,Generic
from typing import Any, Self 
from typing import Annotated
from types  import UnionType, GenericAlias
from contextlib  import contextmanager, ExitStack
from contextvars import ContextVar
from collections import OrderedDict,defaultdict
class _unset():...
class _defaultdict(dict):
    def __missing__(self,key):
        ret = self[key] = ContextVar('key', default=None)
        return ret
context : dict[ContextVar] = _defaultdict()

class defered_archtype:
    ''' Class to construct lists with after intial structure definition '''
    types : list[Any]

    def __init_subclass__(cls):
        cls.types = []

def collapse_type_chain(ty:list)->list:
    res = []
    if not isinstance(ty,(tuple,list,set)):
        return [ty]
    for x in ty:
        if x.__class__ is UnionType:
            for e in x.__args__:
                res.extend(collapse_type_chain(e))
        if x.__class__ is Annotated:
            for e in x.__args__:
                res.extend(collapse_type_chain(e))
        if issubclass(x,defered_archtype):
            for e in x.types:
                res.extend(collapse_type_chain(e))
        else:
            res.append(x)
    return res

# class flat_meta_ref():
#     'allows references across bins, operates in the same way as flat_ref otherwise'
#     ...

class io[*types]:
    ...

class flat_col[key,*bt]:
    '''Collection notation, blind to what bins are importing as. if hasattr(inst.attr,'_import|export|append_col_') it is used instead of the generic interface with reference to the bin to add items to '''
    inst  : Any
    attr  : str
    key   : str
    _type : Any

    def _io_bin_id_(self,bin):
        return hash(self)

    @classmethod
    def from_generic_alias(cls,inst,attr,genericA):
        key, *_type   = genericA.__args__
    
        if isinstance(key,ForwardRef):
            key = key.__forward_arg__
        elif key is Self:
            key = getattr (inst,'_io_bin_name_',inst.__name__)
            types = list(types)
            types.insert(0,inst.__class)

        else:
            _type = key
            key = getattr (key,'_io_bin_name_',key.__name__)
        
        return cls(inst=inst,attr=attr,key=key,_type=_type)

    def __init__(self,*,inst:Any,attr:str,key:str,_type:Any):
        self.inst  = inst
        self.attr  = attr
        self.key   = key
        self._type = _type
        self.data  = {}

    def _import_(self,data:dict[str]):
        self._orig_data = data

        _bin = context[self.key].get() 

        if (inst:=getattr(self.inst, self.attr,_unset)) is _unset:
            if func := getattr(self._type,'_io_cls_import_raw_data_',None):
                inst , data = func(self.data, _bin)
                self.data = data
                setattr(self.inst,self.attr,inst)
                return
            
            inst = self._type()
            setattr(self.inst,self.attr,inst)
            
            if func := getattr(self._type,'_io_import_raw_data_',None):
                self.data = func(self.data, _bin)
                return
                
        for k,v in data.items():
            self.data[k] = _bin.get_data(v)
                #Getting the instance imported by the bin
        
        self.io_like_import(self.data,inst)

    def _export_(self)->dict:

        if (inst := getattr(self.inst,self.attr,_unset)) is _unset:
            return _unset

        
        _bin = context[self.key].get()

        if func:=getattr(inst,'_io_export_raw_data_',None):
            return func(self.data, _bin)
        else:
            return self.io_like_export(inst,_bin)
        

    def io_like_export(self,inst,_bin)->dict:
        ret = {}
        if getattr(inst,'_io_dict_like_',False) or isinstance(inst,(dict,OrderedDict,defaultdict)) or (hasattr(inst,'__getitem__') and hasattr(inst,'__setitem__')):
            for k,v in inst.items():
                ref_key = _bin.add_data(self,v)
                ret[k] = ref_key
        elif getattr(inst,'_io_list_like_',False) or isinstance(inst,(list)):
            for v in inst:
                ref_key = _bin.add_data(self,v)
                ret[k] = ref_key
        else:
            raise Exception('Criteria not met for collection! Must have _io_dict|list_like_ or relvent methods ')
        return ret
    def _append_(self):
        ...
    
    @staticmethod
    def io_like_import(data, inst):
        if getattr(inst,'_io_dict_like_',False) or isinstance(inst,(dict,OrderedDict,defaultdict)) or (hasattr(inst,'__getitem__') and hasattr(inst,'__setitem__')):
            for k,v in data.items():
                inst[k] = v
        elif getattr(inst,'_io_list_like_',False) or isinstance(inst,(list)):
            for k,v in data.items():
                inst.append(v)
        else:
            raise Exception('Criteria not met for collection! Must have _io_dict|list_like_ or relvent methods ')
        

class flat_ref[key,*t]:
    ''' Thrower/Catcher of a type reference to a bin, replaces on disc with _io_bin_id_ or hash '''
    inst  : Any
    attr  : str
    key   : str
    types : tuple[Any]

    @classmethod
    def from_generic_alias(cls,inst,attr,genericA):
        key, *types   = genericA.__args__
    
        if isinstance(key,ForwardRef):
            key = key.__forward_arg__
        elif key is Self:
            key = getattr (inst,'_io_bin_name_',inst.__class__.__name__)
            types = list(types)
            types.insert(0,inst.__class__)
        else:
            key = getattr (key,'_io_bin_name_',key.__name__)
            types = list(types)
            types.insert(0,key)

        if not types:
            types = (Any,)

        return cls(inst=inst,attr=attr,key=key,types=types)
    
    def __init__(self,*,inst:Any,attr:str,key:str,types:tuple):
        self.inst  = inst
        self.attr  = attr
        self.key   = key
        self.types = types

    def _export_(self)->str:
        ''' Add data and return key, let bin take care of ensuring data is singular and in a collection '''
        data = getattr(self.inst, self.attr, _unset)
        if data is _unset: return _unset
        return context[self.key].get().get_data_key(data)

    def _import_(self,data:str):
        ''' Add import_deferend to attach reference after bin is closed '''
        raise Exception('IMPORT CALLED ON REF')
        bin = context[self.key].get()
        def import_defered():
            setattr(self.inst,self.attr,bin.get_data(data))
        bin.add_defered(import_defered)

    def _append_(self,data):
        if func := getattr(getattr(self.inst, self.attr, None),'_append_',None):
            func(data)
        elif data:
            raise('Flat_Refs purpose is indeterminate with append, as obj doesnt have _append_ function to handle data')

class flat_bin[key,*t]:
    inst  : Any
    attr  : str
    key   : str
    types : tuple[Any]

    @classmethod
    def from_generic_alias(cls,inst,attr,genericA):
        key, *types   = genericA.__args__
    
        if isinstance(key,ForwardRef):
            key = key.__forward_arg__
        elif key is Self:
            key = getattr (inst,'_io_bin_name_',inst.__name__)
            types = list(types)
            types.insert(0,inst.__class)

        else:
            key = getattr (key,'_io_bin_name_',key.__name__)
            types = list(types)
            types.insert(0,key)
        if not types:
            types = (Any,)

        return cls(inst=inst,attr=attr,key=key,types=types)
    
    def __init__(self,*,inst:Any,attr:str,key:str,types:tuple):
        self.inst  = inst
        self.attr  = attr
        self.key   = key
        self.types = types
        self.data  = {} 
        self._defered = []

    def add_data(self,col,item)->str|tuple:
        ''' Add data to this bin, requires source from collection. References defer to getting key'''
        if item in self.data.values():
            k_l = [k for k,v in self.data.items() if v == item]
            return k_l[0]
        
        assert not getattr(item,'__io_in_bin__',None)
        item.__io_in_bin__ = self
        
        _val = getattr(item,'__io_in_col__',[])
        item.__io_in_col__ = _val.append(col._io_bin_id_)
        
        if func:=getattr(item,'_io_bin_id_',None):
            key = func(self)
        else:
            key = hash(item)

        if key in self.data.keys():
            raise Exception(f'Bin ({self.inst} : {self.key}) Contains two items by the same key of {key} with different instances')
        
        self.data[key] = item
        
        return key
    
    def get_data_key(self,item):
        assert item in self.data.values()
        k_l = [k for k,v in self.data.items() if v == item]
        return k_l[0]

    def get_data(self,ref:str)->Any:
        ''' Get already type instance imported data on bin close using key exported from get_data_key '''
        return self.data[ref]

    def add_defered(self,defered_function):
        self._defered.append(defered_function)

    def resolve_defered(self):
        for x in self._defered:
            x()

    @contextmanager
    def _context_(self,mode:str='export'):
        assert mode in ['export','import','append']

        try:
            t = context[self.key].set(self)
            yield
            if mode in ['import','append']: self.resolve_defered()
            if mode in ['export']:          self.assert_all_from_collections()
        except:
            raise
        context[self.key].reset(t)
    
    def assert_all_from_collections(self):
        for k,v in self.data.items():
            if not hasattr(v,'__io_in_col__'):
                raise Exception(f"{v}, WAS NOT NOTED TO BE IN A COL")

    def _import_(self,data):
        ret = {}
        if attr_data := getattr(self.inst,self.key,None):
            self.import_incorperate_attr_data(attr_data,src_data=data)
        for k,v in data.items():
            ret[k] = self._import_indv_(v)
        self.data = ret

        return ret
    
    def _import_indv_(self,value):
        for ty in collapse_type_chain(self.types):
            if func := getattr(ty,'__io_bin_match_ref__'):
                if func(value):
                    return ty._io_bin_import_from_data_(value)
                else:
                    continue
            else:
                return ty(value)
        raise Exception('No Types were defined on col!')
                        
    def _append_(self,):
        ...

    def _export_(self)->dict:
        ret = {}
        for k,v in self.data_generator(self.data):
            ret[k]=v._export_()
        return ret

    def data_generator(self, data:dict, used_keys=None):
        ''' Iterate over dict keys, yielding any new results per iteration. '''
        if used_keys is None: used_keys = []
        for k in [x for x in data.keys()]:
            if k in used_keys: continue
            used_keys.append(k)
            yield k, data[k]
        if len(data.keys()) > len(used_keys):
            for x in self.data_generator(data,used_keys):
                yield x


class BaseModel:
    _io_bin_name_ : str

    __io_orig_fields__ : dict[str,Any] 
    __io_orig_bins__   : dict[str,flat_bin]
    __io_orig_cols__   : dict[str,flat_col]
    __io_orig_refs__   : dict[str,flat_ref]
        #All derived from __anotations__ 

    __io_bins__      : dict[str,flat_bin]
    __io_cols__      : dict[str,flat_col]
    __io_refs__      : dict[str,flat_ref]

    _io_list_like_   : bool 
    _io_dict_like_   : bool
        # for as field io on generic custom collection classes, including as a flat_bin-flat_col contributer
        # If used, iterates through using io method and stores as special field on export, re-applies on import
        # Data field must be untyped or blacklisted

    _io_export_defaults_ : bool = False
    _io_whitelist_       : list[str]
    _io_blacklist_       : list[str]
        
    _io_strict_           : bool = True
        #Requires generic attributes to be types with the generic 'io'

    @classmethod
    def __io_bin_match_ref__(cls,data):
        return True
    @classmethod
    def _io_bin_import_from_data_(cls,data):
        inst = cls()
        inst._import_(data=data)
        return inst

    def __io_fields__(self,filter_default=False)->dict:
        ''' Returns dict of {attr:type} to export or import, filter whitelist, blacklist, and export_defaults (via) '''
        
        ret = {}

        blacklist = getattr(self,'_io_blacklist_',[])
        if (whitelist:=getattr(self,'_io_whitelist_',None) )is not None:
            for k,v in self.__io_orig_fields__.items():
                if k in whitelist and not k in blacklist:
                    ret[k] = v
        else:
            for k,v in self.__io_orig_fields__.items():
                if not k in blacklist:
                    ret[k] = v
        
        if filter_default:
            _d = self.__dict__.keys()
            ret = {k:v for k,v in ret.items() if k in _d}

        #Need to unwrap any IO types here, as this returns base types.
        _ret = ret
        ret={}
        for k,v in _ret.items():
            if getattr(v,'__origin__',None) is io:
                v : GenericAlias
                ret[k] = v.__args__[0]
            else:
                ret[k] = v

        return ret

    def _io_bin_id_(self,bin):
        return hash(self)
    
    def __init_subclass__(cls):
        cls.__io_setup__()
        
    @classmethod
    def __io_setup__(cls):
        ...
        cls.__io_orig_fields__ = {}
        cls.__io_orig_bins__   = {}
        cls.__io_orig_cols__   = {}
        cls.__io_orig_refs__   = {}
        for k,v in cls.__annotations__.items():
            if src := getattr(v,'__origin__',None):
                if   issubclass(src,flat_ref):
                    cls.__io_orig_refs__[k]=v
                elif issubclass(src,flat_col):
                    cls.__io_orig_cols__[k]=v
                elif issubclass(src,flat_bin):
                    cls.__io_orig_bins__[k]=v
                elif issubclass(src,io):
                    cls.__io_orig_fields__[k]=v
                elif not getattr(cls,'_io_strict_',True):
                    cls.__io_orig_fields__[k]=v

            elif not getattr(cls,'_io_strict_',True):
                cls.__io_orig_fields__[k]=v

    def __io_attach__(self):
        self.__io_bins__ = {}
        self.__io_cols__ = {}
        self.__io_refs__ = {}
        for k,v in self.__io_orig_bins__.items():
            self.__io_bins__[k] = v.__origin__.from_generic_alias(self,k,v)
        for k,v in self.__io_orig_cols__.items():
            self.__io_cols__[k] = v.__origin__.from_generic_alias(self,k,v)
        for k,v in self.__io_orig_refs__.items():
            self.__io_refs__[k] = v.__origin__.from_generic_alias(self,k,v)
            
    @contextmanager
    def __enter_context__(self,mode='export'):
        self.__io_attach__()
        with ExitStack() as stack:
            for v in self.__io_bins__.values():
                stack.enter_context(v._context_(mode=mode))
            try:
                yield
            except: 
                raise 
            return

    def _import_(self,data):
        with self.__enter_context__(mode='import'):
            self.__import_bins__(data)      #imports every bin, which creates all bin held references (and imports those recursivly) 
            self.__import_cols__(data)      #imports each col, fed from context bins populated by import_bins
            self.__import_refs__(data)      #imports each reference, pointing to bin held item by key
            self.__import_fields__(data)    #imports each field(recur if isintance BaseModel or typed as so)

            if getattr(self, '_io_dict_like_',None) and '_DATA_' in data.keys():
                for k,v in data.pop('_DATA_').items(): self[k] = v
            elif getattr(self, '_io_list_like_',None) and '_DATA_' in data.keys():
                for v in data.pop('_DATA_'): self.append(v)


    def _append_(self):
        with self.__enter_context__(mode='append'):
            ...
        
    def __import_bins__(self,data):
        for k,v in self.__io_bins__.items():
            if not k in data.keys(): continue
            v._import_(data[k])

    def __import_cols__(self,data):
        for k,v in self.__io_cols__.items():
            if not k in data.keys(): continue
            v._import_(data[k])
            
    def __import_refs__(self,data):
        for k,v in self.__io_refs__.items():
            if not k in data.keys(): continue
            v._import_(data[k])
            
    def __import_fields__(self,data):
        
        for k,v in self.__io_fields__().items():
            if not k in data.keys(): continue

            existing = getattr(self,k,None)
            if existing is None and issubclass(v,BaseModel):
                if func:=getattr(v,'_io_import_raw_',None):
                    inst = func(data[k])
                    setattr(self,k,inst)
                    return
                else:
                    inst = v()
                    setattr(self,k,inst)
                    existing = inst
            
            if isinstance(existing,(OrderedDict,defaultdict,dict)):
                for k,v in data[k].items(): existing[k] = v
            elif isinstance(existing,(list)):
                for v in data[k]: existing.append(v)

            if issubclass(existing.__class__,BaseModel) or hasattr(existing,'_import_'):
                    existing._import_(data[k])

            elif existing:
                raise Exception(f'Attempting to import ontop of existing structure that does not support import explicitly! {existing}')

            else:
                setattr(self,k,v(data[k]))

    def _export_(self):
        ret = {}
        with self.__enter_context__(mode='export'):     #Enters into bin's context
            ret = ret|(a:=self._export_cols_())
            ret = ret|(a:=self._export_refs_())
            ret = ret|(a:=self._export_fields_())
            ret = ret|(a:=self._export_bins_())              #Resolve bin's export items
        return ret

    def _export_bins_(self):
        ret = {}
        for k,v in self.__io_bins__.items():
            ret[k]=v._export_()
        return ret

    def _export_cols_(self):
        ret = {}
        for k,v in self.__io_cols__.items():
            ret[k]=v._export_()
        return ret
    
    def _export_refs_(self):
        ret = {}
        for k,v in self.__io_fields__().items():
            if (val := getattr(self,k,_unset)) is _unset : continue
            if func:=getattr(val, '_export_',None):
                ret[k] = func()
            else:
                ret[k] = val
        # src = self._export_data_source_()
        # for k,v in self.__refs.items():
        #     if k not in src.keys(): continue
        #     elif src[k] is _unset: continue
        #     ret[k] = v._export_(src[k])
        # if ret:
        #     raise Exception(f'Exported refs {ret}')
        return ret

    def _export_fields_(self):
        ret = {}
        for k,v in self.__io_fields__(self._io_export_defaults_).items():
            if (d:=getattr(self,k,_unset)) is _unset: continue
            if isinstance(d,BaseModel) or hasattr(d,'_export_'):
                ret[k] = d._export_()
            elif isinstance(d,list):
                ret[k] = [x if not hasattr(d,'_export_') else x._export_() for x in d]
            elif isinstance(d,dict):
                ret[k] = {k:v if not hasattr(d,'_export_') else v._export_() for k,v in d.items()}
            else:
                ret[k] = d
        return ret

if __name__ == '__main__':
    class defered_items(defered_archtype):...

    class test_item(BaseModel):
        _io_bin_name_ = 'base_bin'
        _io_strict_ = True
        # def _export_(self):
        #     if not (data:=self.__io_fields__()):
        #         raise Exception()
        name : io[str]
        ref  : flat_ref[Self] = None

        def _io_bin_id_(self, bin):
            return self.name

    class test_col(BaseModel):
        _io_bin_name_  = 'base_bin'
        _io_dict_like_ = True

        def __init__(self):
            self._data = {}
        def __setitem__(self,key,item):
            self._data[key] = item
        def __getitem__(self,key):
            return self._data[key]
        def items(self):
            return self._data.items()

    class test_root(BaseModel):
        col : flat_col[test_col]
        bin : flat_bin['base_bin',defered_items] #type:ignore
        
        def setup(self):
            self.col = test_col()
            self.col['a'] = test_item()
            self.col['b'] = test_item()
            self.col['b'].ref = self.col['a']

            self.col['a'].name = 'A'
            self.col['b'].name = 'B'


    defered_items.types.append(test_item)

    root_a = test_root()
    root_a.setup()

    root_a_rep = root_a._export_()

    root_b = test_root()
    root_b._import_(root_a_rep)
    root_b_rep = root_b._export_()
    # assert root_a_rep == root_b_rep
