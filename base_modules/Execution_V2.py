''' A bundle of Execution modules that sorts features into individual modules for current cognitive simplicity '''

from ..models.struct_module import module
from .Execution_Types import _mixin, item
from .utils.statics   import get_data_uuid, get_file_uid, INVALID_UUID
from contextvars      import ContextVar
from typing import Any
walk_force = ContextVar('walk_force',default=False)



from types import UnionType, FunctionType
from inspect import isclass
class _unset():...

context = ContextVar('execution context', default=defaultDict(default=None))

from typing import Callable, get_type_hints

class unlocked_func_container[RT=Any,FUNC=FunctionType]():
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

class socket_shapes():
    ''' socket value shape get method containers '''
    class mutable[T=Any]():
        def get(cls,socket)->list[T]|T|_unset:
            if socket.Links_Max > 1:
                res = []
                for x in socket.links: 
                    res.append(cls.Resolve(x.out_socket.value, x.out_socket.context.node))
                if res:
                    return res
                else:
                    return _unset
            else:
                if len(socket.links):
                    x = socket.links[0]
                    return (cls.Resolve(x.out_socket.value, x.out_socket.context.node))
                else:
                    return _unset

        @classmethod
        def Resolve(cls,value,src_node):
            value = cls.Wrap_Funcs(value,src_node)
            return value

        def Wrap_Funcs(value,src_node):
            # if isinstance(value,unlocked_func_container):
            #     if not value.src_node == src_node:
            #         value = value.func 
            # The implications of re-wrapping and adjusting key on an unchanged wrapper do not have a strong argument
                # It confuses chain of values
            if isinstance(value,FunctionType):
                ta = get_type_hints(value)
                if 'return' in ta.keys():
                    print('WARNING: Func {} on Node {} was not wrapped. Wrapping!')
                    ty = ta['return']
                else:
                    print('WARNING: Func {} on Node {} was not wrapped and without a return type hint. Wrapping but expect behavioral errors! ')
                    ty = Any
                value = unlocked_func_container(src_node,value,ty,value.__name__)
            return value
        
    class single[T](mutable):
        @classmethod
        def get(cls,socket)->T|_unset:
            ''' Calls upstream socket.value and returns it. 
            Resolves FunctionType|context_function w/a.
            Base is any input formatted, no resolution of functions 
            _unset is returned to allow for fallback values
            '''
            if len(socket.links) == 1:
                s = socket.links[0].out_socket
                cls.Resolve(s.value,s.context.node)
            elif len(socket.links) > 1:
                raise Exception(f'Singular {cls.__name__} is an incorrect shape declaration for multiple input links!')
            else:
                return _unset
                #Allowes default

        @classmethod
        def Resolve[T](cls,value:T,src_node)->T:
            return cls.Wrap_Funcs(value,src_node)

    class multi[T](mutable):
        @classmethod
        def get(cls,socket)->list[T]|_unset:
            ''' Calls upstream [socket.value] and returns it '''
            res = []
            for x in socket.links: 
                res.append(cls.Resolve(x.out_socket.value,x.out_socket.context.node))
            if res:
                return res
            else:
                return _unset
        
        @classmethod
        def Resolve[T](cls,value:T,src_node)->T:
            return cls.Wrap_Funcs(value,src_node)
            
    ##### Consider making st.func/s return the exec/compile of the upstream socket as a wrapped function! #####

    # class func(single):
    #     ''' I do question the sanity of this one, as args, kwargs do not raise errors *and* this is a non-uniform interface'''
    #     @classmethod
    #     def Resolve[T](cls,value:T,src_node)->unlocked_func_container:
    #         if isinstance(value,FunctionType):
    #             value = cls.Wrap_Func(value,src_node)
    #         if not isinstance(value,(unlocked_func_container)):
    #             value = cls.Wrap_Func(lambda *args, **kwargs: value,src_node)
    #         return value
    
    # class funcs(multi):
    #     ''' I do question the sanity of this one, as args, kwargs do not raise errors *and* this is a non-uniform interface'''
    #     @classmethod
    #     def Resolve[T](cls,value:T,src_node)->unlocked_func_container:
    #         if isinstance(value,FunctionType):
    #             value = cls.Wrap_Func(value,src_node)
    #         if not isinstance(value,(unlocked_func_container)):
    #             value = cls.Wrap_Func(lambda *args, **kwargs: value,src_node)
    #         return value

st = socket_shapes



class main(module):
    UID          = 'Core_Execution'
    Label        = 'Core_Execution'
    Desc         = ''' Core execution method  '''
    ChangeLog    = ''' '''
    Version      = '2.0'

    class socket_mixin(_mixin.socket):
        
        Value_Shape   : st.mutable = st.mutable # Statement to make assert shapes/forms
                                                
        Value_Type    : Any|set[Any]|UnionType  # Statemnt of type(s) produced by socket.
        Value_Default : Any = _unset            # Not saved to file.
        Value_Strict  : bool = True

        def Value_Verify(self,value):
            #TODO
            return True 

        #### Constructed Methods & Vars ####
        Call_Cache_Dump : bool = False
        Call_Cache_Load : bool = False

        def Cache_Dump(self,dir):
            ''' Dump cache infor to location w/a, set disc_loc and disc_cached for cache_load'''
        def Cache_Load(self):
            ''' Load cache from disc_loc, set to self.value '''

        From_Value_Type_Whitelist : set|Any
        From_Value_Type_Blacklist : set = set()

        To_Value_Type_Whitelist   : set|Any
        To_Value_Type_Blacklist   : set = set()
            #Works via checking Value_Type
            #Whitelist is opertunistic (any-in:allow), blacklist is pesimistic (any-in:disalllow)

        def __init_subclass__(cls):
            assert getattr(cls,'Value_Type',   _unset) is not _unset
            assert getattr(cls,'Value_Default',_unset) is not _unset

            if isclass((ty:=getattr(cls,'Value_Type'))):
                if issubclass(ty,(st.mutable)):
                    cls.Value_Shape = ty.__origin__
                    cls.Value_Type  = set[ty.__args__]
            else:
                assert isinstance(cls.Value_Type,(list,set,tuple))

            super().__init_subclass__()

            
        In_Value_Resolution_Chain  = {'value_graph','user_value','value_default','Value_Default'}
        Out_Value_Resolution_Chain = {'value_graph'}
            #these could be a property for custom things that connect to UI



    class node_mixin(_mixin.node):
        Deterministic   : bool
            # Any calls directly to this node will be re-run
            # Invalidates disc cachable ie Is not sharable
            # non-Determ is memo'd at evaluation in the context of the reader/executer (socket)
        Result_Deterministic : bool = True
            #Refers to the assumption if a resulting function is deterministic or not

        Mem_Cachable    : bool #= True
        Disc_Cachable   : bool #= True
            # Values to invalidate disc/mem cachable inherited from the output sockets
            # Check against all output sockets being disc cachable to verify. Otherwise throw an error.

        disc_cached   : bool = False
        disc_location : str
            #wrapper will utilize this




    class exec_node_mixin(_mixin.exec_node):
        def execute(): ...

    class placeholder_node_mixin(_mixin.exec_placeholder_node):
        def execute(): ...
        
    class meta_node_mixin(_mixin.meta_node):
        def compile(): ...

