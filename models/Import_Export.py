from contextvars import ContextVar
from contextlib  import contextmanager, ExitStack
from typing import Self, Any, Type, ForwardRef
from typing import get_args as get_generic_args
from types import GenericAlias, FunctionType
from typing import _GenericAlias

class _defaultdict(dict):
    def __missing__(self,key):
        res = self[key] = ContextVar(key,default=None)
        return res

context : _defaultdict[ContextVar['flat_ref_col']] = _defaultdict()

class flat_ref_col[T,key]:
    ''' Collection of Items found in children's structures That match type/keyword '''
    ''' Type as ty is required to create instances on import '''

    data      : dict
    container : Any
    attr      : str
    ty        : T
    key       : str
    delayed_references : list[FunctionType]

    def __init__(self,container,attr,T=None,key=None):
        self.container = container
        self.attr      = attr
 
        if T is Self: self.ty = container
        elif T      : self.ty = T
        else        : raise Exception('Missing Type!')

        if key:  self.key = key
        else:    self.key = attr

        self.delayed_references = []

        self.data = {}
    
    @contextmanager
    def in_context(self):
        try:
            token = context[self.key].set(self)
            yield
        except:
            raise
        finally:
            self._import_delayed_()
            context[self.key].reset(token)

    def _export_(self)->dict:
        ret = {}
        for k,v in self.data.items():
            ret[k] = v._export_()
        return ret

    def _import_(self, data:dict):
        assert isinstance(data,dict)
        for k,v in data.items():
            obj = self.ty()
            obj._import_(v)
            self.data[k] = obj

    def _import_delayed_(self):
        ''' References are delayed on import until every object has been imported '''
        for x in self.delayed_references: x()
    
            
class flat_ref[T,key]:
    ''' Reference that tells what contextually keyed collection to place the object in or get from. '''
    ''' Stored it is a hash_string, same as key of collection '''
    ''' Convert a generic type to an instance at runtime '''
    data : dict
    container : Any
    attr      : str
    ty        : T
    key       : str

    def __init__(self,container,attr,T=None,key=None):
        self.container = container
        self.attr      = attr
 
        if T is Self: self.ty = container
        elif T      : self.ty = T
        else        : raise Exception('Missing Type!')

        if key:  self.key = key
        else:    self.key = attr
    
    def _export_(self,data:Any)->str:
        data_key = hash(data)
        context[self.key].get().data[data_key] = data
        return data_key
    
    def _import_(self,inst,ref:str):    
        # assert isinstance(ref,str)

        col = context[self.key].get()#.data[ref]
        def _import_func_():
            self._import_delayed_(inst,col,ref)

        col.delayed_references.append(_import_func_) 

    def _import_delayed_(self,inst, col : flat_ref_col, ref:str):
        setattr(inst,self.attr,col.data[ref])

class BaseModel:
    ''' Model to inherit  '''
    __fields : dict[str,Type]
    __refs   : dict[str,flat_ref]
    __colls  : dict[str,flat_ref_col]
    #TODO functionality:
    # __alias  : dict[str,tuple[str]]
    # __export_props : bool = False
    # __duck_typing  : bool = False

    def _export_(self)->dict:
        self._localize_cols_()
        ret={}
        with ExitStack() as stack:
            for k,v in self.__colls.items():
                stack.enter_context(v.in_context())

            for k,v in self.__fields.items():
                val = getattr(self,k,None)
                if isinstance(val,BaseModel):
                    ret[k]=val._export_()
                else:
                    ret[k]=val

            for k,v in self.__refs.items():
                if val:=getattr(self,k,None):
                    ret[k]=v._export_(val)

            for k,v in self.__colls.items():
                ret[k]=v._export_()
            
            return ret
            
    def _import_(self,data:dict):
        ''' Load data onto self, recur as req '''
        self._localize_cols_()
        data_keys = data.keys()
        with ExitStack() as stack:
            for k,v in self.__colls.items():
                stack.enter_context(v.in_context())

            for k,v in self.__colls.items():
                if k not in data_keys: continue
                val = data[k]
                v._import_(val)

            for k,v in self.__fields.items():
                if k not in data_keys: continue
                val = data[k]
                ty = self.__annotations__[k]

                if   isinstance(ty,GenericAlias):
                    setattr(self,k,val)

                elif ty is Self:
                    obj = self._import_root_(val)
                    setattr(self, k, obj)

                elif issubclass(ty,BaseModel):
                    obj = ty._import_root_(val)
                    setattr(self, k, obj)

                elif issubclass(ty,flat_ref):
                    ty._import_(val)

                else:
                    setattr(self,k,ty(val))

            for k,v in self.__refs.items():
                if k not in data_keys: continue
                val = data[k]
                if not val:
                    continue
                v._import_(self,val)

            for k,v in self.__colls.items():
                v._import_delayed_()

    @classmethod
    def _import_root_(cls,data:dict|None):
        if data is None:
            return None 
        inst = cls()
        inst._import_(data)
        return inst

    def _localize_cols_(self):
        self.__colls = {}
        for k,v in self.__base_colls.items():
            ty, key = get_generic_args(v)
            key = key.__forward_arg__
            obj = v.__origin__(self,k,ty,key)
            self.__colls[k]=obj

    def __init_subclass__(cls):
        cls.__fields = {}
        cls.__refs   = {}
        cls.__base_colls = {}

        ''' instance each flat_ref_col '''
        for k,v in cls.__annotations__.items():
            if isinstance(v,_GenericAlias):

                if issubclass(v.__origin__, flat_ref_col):
                    cls.__base_colls[k] = v

                elif issubclass(v.__origin__, flat_ref):
                    ty, key = get_generic_args(v)
                    key = key.__forward_arg__
                    obj = v.__origin__(cls,k,ty,key)
                    cls.__refs[k] = obj

                else:
                    cls.__fields[k] = v
            
            else:
                cls.__fields[k] = v
        
        



class B(BaseModel):
    # def __init__(self,name):
    #     self.name = name
    relative_target : flat_ref[Self,'b_coll'] = None
    name : str

class A(BaseModel):
    b_coll : flat_ref_col[B,'b_coll']
    # b_struct : flat_ref[Self,'b_coll'] = B()
    b_struct : B
    a_struct : Self
    
    def __init__(self):
        b = B()
        b.name = 'B1'
        b.relative_target = B()
        b.relative_target.name = 'B2'
        self.b_struct = b

obj = A()
obj.a_struct = A()

print(val_a := obj._export_() )

obj_b  = A._import_root_(val_a)

print(val_b := obj_b._export_() )
# assert val_a == val_b
