from ..models.struct_module_types import mixin,_mixin
from ..models.struct_module_types import item as _item


class exec_metadata():
    ''' Metadata for display, stats and debug '''
    metanode_uid     : str
    from_cache       : bool
    # execution_time   : bool 
    compile_cache    : dict

class meta_metadata():
    ...
    
from inspect import isclass
from ..statics import _unset

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

class mixin(mixin):
    class exec_node(_mixin.node):
        _constr_bases_key_ = 'node:exec_node'
    class meta_node(_mixin.node):
        _constr_bases_key_ = 'node:meta_node'
    class exec_placeholder_node(_mixin.node):
        _constr_bases_key_ = 'node:placeholder_node'

class _mixin(mixin,_mixin): ...

class item(_item):
    #TODO: Add facotry methods!
    
    class socket(_item.socket):
        def __init_subclass__(cls):
            assert getattr(cls,'Value_Type',   _unset) is not _unset
            assert getattr(cls,'Value_Default',_unset) is not _unset

            if isclass((ty:=getattr(cls,'Value_Type'))):
                if issubclass(ty,(socket_shapes.mutable)):
                    cls.Value_Shape = ty.__origin__
                    cls.Value_Type  = set[ty.__args__]
            else:
                assert isinstance(cls.Value_Type,(list,set,tuple))
            super().__init_subclass__()
        ...

    class exec_node(_item.node):
        ''' Execution node base. '''
        _constr_bases_key_ = 'node:exec_node'

        def __init_subclass__(cls):
            # assert hasattr(cls.Deterministic)

            super().__init_subclass__()

        #### User Constructed Values ####
        
        Deterministic : bool
        Disc_Cachable : bool
        Cacheable     : bool


        #### Attributes ####
                 
        # uuid : str  #Fullfilled via collection
        chain_deterministic : bool          = True
        metadata            : exec_metadata

        value_sum           : property
        _value_sum          : str|list[str]
        walk_sum            : property
        _walk_sum           : str

        def execute(self):
            raise Exception('Execution Has Not Been Defined!')

    
    class meta_node(_item.node):
        _constr_bases_key_ = 'node:meta_node'
        def compile():...
        
    class exec_placeholder_node(_item.node):
        _constr_bases_key_ = 'node:placeholder_node'
        def execute():...


