from typing import get_args, Any, Self, Callable
from types import UnionType
from contextlib  import contextmanager, ExitStack
from contextvars import ContextVar
from typing import Self

class _defaultdict(dict):
    def __missing__(self,key):
        ret = self[key] = ContextVar('key', default=None)
        return ret

context : dict[ContextVar] = _defaultdict()

class _unset:...

def collapse_type_chain(inst,ty)->list:
    res = []
    for x in ty:
        if x.__class__ is UnionType:
            for e in x.__args__:
                res.extend(collapse_type_chain(e))
        else:
            res.append(x)
    return res

class flat_ref[key,*T]:
    @classmethod
    def _from_generic_alias_(cls, inst, attr, generic):
        key, *ty = get_args(generic)
        return cls(inst,attr,key,*ty)

    def __init__(self,inst,attr,key,*ty):
        self.inst = inst
        self.attr = attr
        self.key   = key
        self.type_chain = collapse_type_chain(inst,ty)
    
    def _export_(self,src_data):
        # elif isinstance(val,model):
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
    
    def __init__(self,inst,attr,key,*ty):
        self.inst = inst
        self.attr = attr
        self.key   = key
        self.type_chain = collapse_type_chain(inst,ty)
        
        self.data = {}
        self.import_defered = []


        if len(ty)>1: self.type_fallback = ty[-1]
        else:         self.type_fallback = None

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
        for k,v in data.items():
            ret[k] = self._import_indv_(v)
        self.data = ret
        print(f'Col Import: {ret}')
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
            

    def _export_(self)->dict:
        ret = {}
        for k,v in self.data.items():
            val=v._export_()
            if val is _unset: continue
            else: ret[k]=val
        return ret

    import_defered : list[Callable]
    def _import_defered_(self):
        for x in self.import_defered: x()
    

class model:
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

    def _export_coll_id_(self):
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
        for k,v in self.__fields.items():
            if k in data.keys():
                if issubclass(v,model):
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
            
            if isinstance(src[k],model):
                ret[k] = src[k]._export_()
            else:
                ret[k] = src[k]
        return ret

#TODO: Create model that's compatable with lists/dir and acts as a collection.
#Customized _import_/_export_ required.

if __name__ == '__main__':
    
    class B(model):
        name   : str
        b_ref  : flat_ref['b_coll'] = None

    class A(model):
        name   : str
        b_coll : flat_col['b_coll',B]
        b_ref  : B

    
    a1_inst = A()
    a1_inst.name = 'a1_inst'
    a1_inst.b_ref = B()
    a1_inst.b_ref.name = 'b1_inst'
    a1_inst.b_ref.b_ref = B()
    a1_inst.b_ref.b_ref.name = 'b2_inst'

    a1_val = a1_inst._export_()
    print(a1_val)
    a2_inst = A._import_from_data_(a1_val)
    print('br_ef:',a2_inst.b_ref)
    print(a2_inst._export_())

    