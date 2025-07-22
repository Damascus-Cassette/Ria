from typing import get_args, Any, Self, Callable
from types import UnionType
from contextlib  import contextmanager, ExitStack
from contextvars import ContextVar
from typing import Self, ForwardRef

from collections import OrderedDict,defaultdict

class _defaultdict(dict):
    def __missing__(self,key):
        ret = self[key] = ContextVar('key', default=None)
        return ret

context : dict[ContextVar] = _defaultdict()

class _unset:...

class defered_archtype:
    ''' Class to construct lists with after intial structure definition '''
    types : list[Any]

    @classmethod
    def append(cls,item):
        cls.types.append(item)

class context_archtype:
    ''' Class to construct lists with after intial structure definition via attr 'types' as a context varaible '''
    _context_key_ : str
    types : ContextVar[list]

    def __init_subclass__(cls):
        cls._types = ContextVar(getattr(cls,'_context_key_',cls.__name__), default = [])
    
    @classmethod
    def append(cls,item):
        cls.types.get().append(item)

    @classmethod
    @contextmanager
    def _as(cls,types:list=None):
        if types is None:
            types = []
        t = cls.types.set(types)
        yield
        cls.types.reset(t)

def collapse_type_chain(ty)->list:
    res = []
    for x in ty:
        if x.__class__ is UnionType:
            for e in x.__args__:
                res.extend(collapse_type_chain(e))
        if issubclass(x,defered_archtype):
            for e in x.types:
                res.extend(collapse_type_chain(e))
        elif issubclass(x,context_archtype):
            for e in x.types.get():
                res.extend(collapse_type_chain(e))
        else:
            res.append(x)
    return res

class flat_ref[key,*T]:
    @classmethod
    def _from_generic_alias_(cls, inst, attr, generic):
        key, *ty = get_args(generic)
        return cls(inst,attr,key,*ty)

    def __init__(self,inst,attr,key:ForwardRef,*ty):
        self.inst = inst
        self.attr = attr
        self.key   = key.__forward_arg__
        self.type_chain = collapse_type_chain(ty)
    
    def _export_(self,src_data):
        # elif isinstance(val,BaseModel):
        if func:=getattr(src_data,'_export_coll_id_',None):
            data_key = func(src_data)
        else:
            data_key = hash(src_data)

        context[self.key].get().data[data_key] = src_data
        return data_key

    def _import_(self,ref:str|int):
        col = context[self.key].get()
        def _import_delayed_():
            setattr(self.inst,self.attr,col.data[ref])
        col.import_defered.append(_import_delayed_)
    

class flat_col[key,*T]:
    inst        : Any
    attr        : str
    key         : str|int
    type_chain  : tuple[Any]

    @classmethod
    def _from_generic_alias_(cls, inst, attr, generic):
        key, *ty = get_args(generic)
        return cls(inst,attr,key,*ty)
    
    def __init__(self,inst,attr,key:ForwardRef,*ty):
        self.inst = inst
        self.attr = attr
        self.key   = key.__forward_arg__
        self._type_chain = ty
        
        self.data = {}
        self.import_defered = []


        if len(ty)>1: self.type_fallback = ty[-1]
        else:         self.type_fallback = None

    @property
    def type_chain(self):
        return [x for x in collapse_type_chain(self._type_chain)]

    @contextmanager
    def _import_context_(self):
        try:
            t = context[self.key].set(self)
            yield
            self._import_defered_()
        except:
            raise
        finally:
            context[self.key].reset(t)
    
    @contextmanager
    def _export_context_(self):
        try:
            t = context[self.key].set(self)
            yield
        except:
            raise
        finally:
            context[self.key].reset(t)
    

    def _import_(self,data):
        ret = {}
        if attr_data := getattr(self.inst,self.key,None):
            self.import_incorperate_attr_data(attr_data,src_data=data)
        for k,v in data.items():
            ret[k] = self._import_indv_(v)
        self.data = ret

        return ret
    
    def _import_indv_(self,value):
        for ty in self.type_chain:
            if func := getattr(ty,'_match_ref_type_'):
                if func(value):
                    return ty._import_from_data_(value)
                else:
                    continue
            else:
                return ty(value)
        raise Exception('No Types were defined on col!')

    import_defered : list[Callable]    
    def _import_defered_(self):
        for x in self.import_defered: x()

    def import_incorperate_attr_data(self,attr_data,import_data):
        if func:=getattr(attr_data,'__flat_col_import_incorperate__',None):
            func(self)
        elif (isinstance(attr_data,(dict, defaultdict, OrderedDict)) or getattr(attr_data, '__flat_col_dict__',False)):
            self.import_incorperate_dict_like(attr_data, import_data)
        elif (isinstance(attr_data,(list,tuple,set)) or getattr(attr_data, '__flat_col_list__',False)): 
            self.import_incorperate_list_like(attr_data, import_data)
        else:
            raise Exception(f'Could not incorperate data to {attr_data} from {import_data}!')

    def import_incorperate_dict_like(self,attr_data,src_data:dict):
        for k,v in src_data.items():
            if k in attr_data.keys():
                raise Exception(f'Trying to double import {k} on {attr_data}')
            attr_data[k] = v

    def import_incorperate_list_like(self,attr_data,src_data:dict):
        for k,v in self.src_data.items():
            if v in attr_data:
                raise Exception(f'Trying to double import {k} on {attr_data}')
            attr_data.append(k)     


    def _export_(self,attr_data=None)->dict:
        ret = {}
        if attr_data:
            self.export_incorperate_attr_data(attr_data)
        for k,v in self.data_generator(self.data):
            val=v._export_()
            ret[k]=val
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

    def export_incorperate_attr_data(self,attr_data):
        if func:=getattr(attr_data,'__flat_col_export_incorperate__',None):
            func(self)
        elif (isinstance(attr_data,(dict, defaultdict, OrderedDict)) or getattr(attr_data, '__flat_col_dict__',False)):
            self.export_incorperate_dict_like(attr_data)
        elif (isinstance(attr_data,(list,tuple,set)) or getattr(attr_data, '__flat_col_list__',False)): 
            self.export_incorperate_list_like(attr_data)
        else:
            raise Exception(f'Could not incorperate data from src {attr_data}!')

    def export_incorperate_dict_like(self,data):
        for k,v in data.items():
            if k in self.data.keys():
                if self.data[k] is not v:
                    raise Exception(f'Two Referenced Entities are not the same but have the same key! {k} : {self.data[k]} != {v}')
                continue
            self.data[k] = v
    
    def export_incorperate_list_like(self,data):
        for item in data:
            if func:=getattr(item,'_export_coll_id_',None):
                k = func(item)
            else:
                k = hash(item)
            
            if k in self.data.keys():
                if self.data[k] is not k:
                    raise Exception(f'Two Referenced Entities are not the same but have the same key! {k} : {self.data[k]} != {item}')
                continue
            self.data[k] = item



    

class BaseModel:
    __export_cls_vars__ : bool = False
    #does not export unset/deleted variables

    __orig_cols : dict[str,flat_col]
    __orig_refs : dict[str,flat_ref]

    __cols      : dict[str,flat_col]
    __refs      : dict[str,flat_ref]
    __fields    : dict[str,Any]

    @classmethod
    def _match_ref_type_(cls,value):
        return True
    
    @classmethod
    def _import_from_data_(cls,data):
        inst = cls()
        inst._import_(data)
        return inst

    def _localize_cols_(self):
        self.__cols = {}
        for k,v in self.__orig_cols.items():
            self.__cols[k] = v._from_generic_alias_(self,k,v)
    def _localize_refs_(self):
        self.__refs = {}
        for k,v in self.__orig_refs.items():
            self.__refs[k] = v._from_generic_alias_(self,k,v)

    def __init_subclass__(cls):
        cls.__orig_cols = {} 
        cls.__orig_refs = {} 
        cls.__fields = {}
        for k,v in cls.__annotations__.items():
            if src := getattr(v,'__origin__',None):
                if   issubclass(src,flat_ref):
                    cls.__orig_refs[k]=v
                elif issubclass(src,flat_col):
                    cls.__orig_cols[k]=v
                else:
                    cls.__fields[k]=v 
            else:
                cls.__fields[k]=v
        # print(f'INIT SUBCLASS {cls}')
        # print('__orig_cols' , cls.__orig_cols)
        # print('__orig_refs' , cls.__orig_refs)
        # print('__fields' , cls.__fields)
        # print(f'------')

    @contextmanager
    def _import_context_(self):
        with ExitStack() as stack:
            for k,v in self.__cols.items():
                stack.enter_context(v._import_context_())
            yield
    @contextmanager
    def _export_context_(self):
        with ExitStack() as stack:
            for k,v in self.__cols.items():
                stack.enter_context(v._export_context_())
            yield
    
    def _import_(self,data):
        self._localize_cols_()
        self._localize_refs_()
        with self._import_context_():
            self._import_cols_(data)
            self._import_fields_(data)
            self._import_refs_(data)

    def _export_coll_id_(self,coll):
        return hash(self)  
    
    def _export_(self)->dict:
        ret = {}
        self._localize_cols_()
        self._localize_refs_()
        with self._export_context_():
            ret = ret|self._export_fields_()
            ret = ret|self._export_refs_()
            ret = ret|self._export_cols_()
        return ret
    
    def _export_data_source_(self)->dict:
        if self.__export_cls_vars__:
            return {k:getattr(self,k,_unset) for k in dir(self)}
        else:
            return vars(self)
        
    def _import_cols_(self,data):
        for k,v in self.__cols.items():
            if k in data.keys():                
                v._import_(data[k])
            
    def _import_refs_(self,data):
        for k,v in self.__refs.items():
            if k in data.keys():
                v._import_(data[k])

    def _import_fields_(self,data):
        #TODO: Consider
        for k,v in self.__fields.items():
            if k in data.keys():
                existing = getattr(self,k,None)
                if issubclass(existing.__class__,BaseModel) or hasattr(existing,'_import_'):
                    existing._import_(data[k])
                elif func:=getattr(existing, '__flat_col_import_incorperate__',None):
                    func(data[k])                
                elif getattr(existing, '__flat_col_dict__',None) or isinstance(existing,(OrderedDict,defaultdict,dict)):
                    #TODO get method from flat_col
                    raise Exception ('TODO: add functionality')
                elif getattr(existing, '__flat_col_list__',None) or isinstance(existing,(list)):
                    #TODO get method from flat_col
                    raise Exception ('TODO: add functionality')
                elif existing:
                    raise Exception(f'Attempting to import ontop of existing structure that does not support import explicitly! {existing}')
                elif issubclass(v,BaseModel) or hasattr(v,'_import_from_data_'):
                    setattr(self,k,v._import_from_data_(data[k]))
                else:
                    setattr(self,k,data[k])


    def _export_cols_(self):
        ret = {}
        src = self._export_data_source_()
        for k,v in self.__cols.items():
            if k not in src.keys():
                ret[k] = v._export_()
            elif src[k] is _unset:
                ret[k] = v._export_()
            else:
                ret[k] = v._export_(src[k])
        return ret
    
    def _export_refs_(self):
        ret = {}
        src = self._export_data_source_()
        for k,v in self.__refs.items():
            if k not in src.keys(): continue
            elif src[k] is _unset: continue
            ret[k] = v._export_(src[k])
        # if ret:
        #     raise Exception(f'Exported refs {ret}')
        return ret
            
    def _export_fields_(self):
        src = self._export_data_source_()
        ret = {}
        for k,v in self.__fields.items():
            if k not in src.keys(): continue
            elif src[k] is _unset: continue
            
            d = src[k]
            if isinstance(d,BaseModel) or hasattr(d,'_export_'):
                ret[k] = d._export_()
            elif isinstance(d,list) or getattr(d,'__flat_col_list__',False):
                ret[k] = [x if not hasattr(d,'_export_') else x._export_() for x in d]
            elif isinstance(d,dict) or getattr(d,'__flat_col_dict__',False):
                ret[k] = {k:v if not hasattr(d,'_export_') else v._export_() for k,v in d.items()}
            else:
                ret[k] = src[k]
        return ret

#TODO: Create BaseModel that's compatable with lists/dir and acts as a collection.
#Customized _import_/_export_ required.

if __name__ == '__main__':
    
    class B(BaseModel):
        def _export_coll_id_(self,coll):
            assert self.name
            return f'< {self.name} >'
        
        name   : str
        b_ref  : flat_ref['b_col'] = None #type:ignore

    class A(BaseModel):
        def _export_coll_id_(self,coll):
            assert self.name
            return f'< {self.name} >'
        
        name   : str
        b_col  : flat_col['b_col',B] #type:ignore
        b_ref  : flat_ref['b_col',B] #type:ignore
        # b_ref  : B  
            #Partially flat, stores first inst on object, rest in bin

    
    a1_inst = A()
    a1_inst.name = 'a1_inst'
    a1_inst.b_ref = B()
    a1_inst.b_ref.name = 'b1_inst'
    a1_inst.b_ref.b_ref = B()
    a1_inst.b_ref.b_ref.name = 'b2_inst'
    b3 = B()
    b3.name = 'b3_inst'
    a1_inst.b_ref.b_ref.b_ref = b3
    a1_inst.b_col = [b3]
        # After _import_ this is filled with all users foudn via the _export_ walk.
        # Since this is greedy by default, consider cross-bin references using a global bin ID or similar and structurally allow a backup greedy bin.
            # Would require a structural re-factor    
    
    a1_val = a1_inst._export_()
    print(a1_val)
    a2_inst = A._import_from_data_(a1_val)
    # print('br_ef:',a2_inst.b_ref)
    print(a2_inst._export_())

    