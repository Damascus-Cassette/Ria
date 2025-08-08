''' This temp file is to write and allow a monad-functional approach through locked and unlocked containers
locked_containers   refer to objects that are function-locked and determined by the module. Possibly disc cachable
unlocked_containers are generic non-disc-cachable containers that must be re-generated per session.

Sockets that return a FunctionType|Lambda not in a container are wrapped in a function's unlocked_container that inherits the node's Determinstic & Mem-Cachable Options.

'''

from ..models.struct_file_io import BaseModel
from ..models.struct_module_types import _item_base

from typing import Any, Self
from types  import FunctionType
from copy   import copy

import inspect

class container_base():
    Module        : Any
    Deterministic : bool #SELF-TYPE|OPERATION will always give the same result (TODO: if false, must memo/job-cache on call) 
    Mem_Cachable  : bool #SELF-TYPE|OPERATION is cachable in memory (If false, gets re-recreated before each time it's called)
    Disc_Cachable : bool #SELF-TYPE           is cachable to disc, only allowed in locked_containers 

    def _Chain_Validator(self, attr:str, contr_attr:str, attr_assume:bool=True)->bool:
        if not getattr(self,attr,attr_assume): return False
        for v in getattr(self,'Contributers',[]):
            if isinstance(v,FunctionType): v = v()    #collapse contributing functions, assuming they are properties. This means that all functions must be turned to unlocked_function_containers
            if not getattr(v,contr_attr,attr_assume): return False
        return True

    #NIT: should these be lowercase since it's instance, or uppercase since it's a reflection on class attributes in instance structure?
    @property
    def _Deterministic(self): return self._Chain_Validator(attr='Deterministic', contr_attr='_Deterministic')
    @property
    def _Mem_Cachable(self):  return self._Chain_Validator(attr='Mem_Cachable',  contr_attr='_Mem_Cachable')
    @property
    def _Disc_Cachable(self): return self._Chain_Validator(attr='Disc_Cachable', contr_attr='_Disc_Cachable')
    
    Contributers  : list[Self|FunctionType] | property
        #FunctionTypes are executed at observation. Must contain no

class locked_data_container[DT](BaseModel, container_base):
    ''' Complex Data Container, useful for custom datastruct interface ops.
    Assumptions are Mem_Cachable, Deterministic, Disc_Cachable are true '''
    Module        : Any
    Deterministic : bool = True #If the SELF.DATA is deterministic 
    Mem_Cachable  : bool = True #If the SELF is Mem-Cachable (Otherwise reconstructs self)
    Disc_Cachable : bool = True #If the SELF.DATA is Disc-Cacahble

    UID           : str
    Version       : str

    def __init_subclass__(cls):
        # TODO: want to align Module checking to be defered to construction phase.
        # assert getattr(cls, 'Module'  , None) is not None
        assert getattr(cls, 'UID'     , None) is not None
        assert getattr(cls, 'Version' , None) is not None

    @classmethod
    def construct[T:Any](cls, UID, Version, DataType:T, **kwargs)->Self[T]:
        kwargs = copy(kwargs)
        # kwargs['Module']   = Module
        kwargs['DataType'] = DataType
        kwargs['UID']      = UID
        kwargs['Version']  = Version
        return type(UID,(cls,),kwargs)

    ####

    data : DT

    def __init__(self,data:DT):
        self.data = data

    @property
    def _hash_(self):
        #TODO : hash from self.data, Self UID, Version and self.Module.uid
        ...


class locked_func_container[FT=FunctionType,RT=Any](BaseModel, container_base):
    Module        : Any

    Deterministic : bool = True #Refers to the result of the SELF.FUNC
    Mem_Cachable  : bool = True #Refers to the SELF object
    Disc_Cachable : bool = True #Refers to the SELF object

    UID           : str
    Version       : str
    DataType      : Any
    Func          : FT
    Func_Include_Container : bool = False
    Result_Disc_Cachable   : bool
        #Refers to the Result being disc-cachable

    def __init_subclass__(cls):
        assert getattr(cls, 'Func'    , None) is not None
        assert getattr(cls, 'UID'     , None) is not None
        assert getattr(cls, 'Version' , None) is not None
        if not getattr(cls,'Deterministic'):
            assert getattr(cls, 'Result_Disc_Cachable', None) #Must be disc-cachable if non-determ

    @classmethod
    def construct[T:FunctionType](cls, UID, Version, Func:T, **kwargs)->Self[T]:
        kwargs = copy(kwargs)

        kwargs['DataType'] = Func
        kwargs['UID']      = UID
        kwargs['Version']  = Version

        #TODO: write DataType!

        return type(UID,(cls,),kwargs)

    @property
    def Contributers(self)->Any:
        for k,v in self.default_kwargs:
            yield v

    default_kwargs : dict

    def __init__(self,**default_kwargs):
        ''' initialize with default kargs, which are evaluted as contibuters. 
        This allows uuid-able observation and monadic-ish chains that can be subverted where required (though def not recomended) '''
        self.default_kwargs = default_kwargs

    def __call__(self,*args,**kwargs)->RT:
        if not self.Determinstic:
            #TODO: Memo & retrieve memo if non-deterministic
            ...

        if self.Func_Include_Container:
            return self.Func(self,*args,**kwargs)
        else:
            return self.Func(*args,**kwargs)
        
    def _hash_():
        #TODO: UID of self and Contrinuters!
        ...
        
class locked_prop_container[RT=Any,FT=FunctionType](locked_func_container):
    ''' Much the same as a locked_func_container, just with a .data property that results are mean to be accessed through.
    Used for clarity in usage of the function provided.
    In current structure, when used in value_hash, the result is computed and utilized in the value_hash.
        This may cause double execution, in cases where context is used. consider changing? 
    as with the func container Non-Deterministic results are tied to _hash_ value and run ONCE per hash, per job for repeatability
    '''

    Module        : Any

    Deterministic : bool = True   #Refers to the result of the SELF.FUNC
    Mem_Cachable  : bool = True   #Refers to the SELF object
    Disc_Cachable : bool = True   #Refers to the SELF object

    UID           : str
    Version       : str
    DataType      : Any
    Func          : FT

    Func_Include_Container : bool = False #If property should have the container passed in
    Result_Disc_Cachable   : bool #Refers to the direct result being disc-cachable

    @property
    def data(self):
        return self()

from typing import Callable

class unlocked_func_container[RT=Any,FUNC=FunctionType](locked_func_container):
    ''' Unlocked func Container that is NEVER Disc-Cachable. Provide UID of function behavior for optimized caching behavior '''

    Module        : Any

    Deterministic : bool        = True   #Refers to the result of the SELF.FUNC
    Mem_Cachable  : bool        = True   #Refers to the SELF object
    Disc_Cachable : bool        = False  #
    Result_Disc_Cachable : bool = True

    UID           : str
    Version       : str
    DataType      : RT
    func          : FUNC

    construct     = None

    def __init_subclass__(cls):
        assert not cls.Disc_Cachable #NEVER on unlocked_func_container
        assert getattr(cls, 'UID'     , None) is not None
        assert getattr(cls, 'Version' , None) is not None
        if not getattr(cls,'Deterministic'):
            assert getattr(cls, 'Result_Disc_Cachable', None) #Must be disc-cachable if non-determ
    
    def __init__[R=Any,F=FunctionType](self, src_node, func:F, return_type:R=Any, f_id='')->Self[R,F]:
        self.f_id = f_id
        self.func = func

        self.Deterministic = src_node.Deterministic
        self.Mem_Cachable  = src_node.Mem_Cachable and src_node.Deterministic

        self.value_hash    = src_node.value_hash 
            #value input of node
            #In cases where a func is built up, it's restung

    # @determ_unknown #memo in job.
    def __call__(self,*args,**kwargs)->RT:
        # if not self.Determinstic:
            #TODO: Memo & retrieve memo if non-deterministic
            # ...

        if self.Func_Include_Container:
            return self.Func(self,*args,**kwargs)
        else:
            return self.Func(*args,**kwargs)
    
