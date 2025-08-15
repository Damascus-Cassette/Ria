''' A bundle of Execution modules that sorts features into individual modules for current cognitive simplicity '''

from .utils.statics         import get_data_uuid, get_file_uid, INVALID_UUID
from .Execution_Types       import _mixin, item
from ..statics              import _unset
from ..models.struct_module import module
from .Execution_Types       import socket_shapes as st
from .Execution_Types       import unlocked_func_container

from typing           import Any, Self, get_type_hints, ForwardRef, TypeAlias, Callable
from types            import UnionType, FunctionType, MethodType
from collections      import defaultdict
from contextvars      import ContextVar
from inspect          import isclass


context = ContextVar('execution context', default=defaultdict(default=None))


class main(module):
    UID          = 'Core_Execution'
    Label        = 'Core_Execution'
    Desc         = ''' Core execution method  '''
    ChangeLog    = ''' '''
    Version      = '2.0'

    class socket_mixin(_mixin.socket):
        #### Constructed Methods & Vars ####
        Value_Shape    : st.mutable  = st.mutable  # Statement to make assert shapes/forms                                                
        Value_In_Types : Any|tuple[Any]|UnionType  # Statemnt of type(s) produced by socket.
        Value_Out_Type : Any                       # Out type must be singular
        Value_Default  : Any = _unset              
            #Note: None above are saved to file.

        In_Value_Resolution_Chain  = ('in_graph_value_getter' ,'user_value','value_default','Value_Default')
        Out_Value_Resolution_Chain = ('out_graph_value_getter',)
            #out_graph_value_getter_errorless can be used for default chains, but not a usual use case

        #TODO: Attributes for caching
        # Deterministic
        # Result_Deterministic
        # Mem_Cachable
        # Disc_Cachable


        #TODO: Defer Impliment bellow secondary implimentation?
        # Call_Cache_Dump : bool = False
        # Call_Cache_Load : bool = False

        # def Cache_Dump(self,dir):
        #     ''' Dump cache infor to location w/a, set disc_loc and disc_cached for cache_load'''
        # def Cache_Load(self):
        #     ''' Load cache from disc_loc, set to self.value '''


        #TODO: Defer Event/Type checking attributes bellow in a type checking module?
        # From_Value_Type_Whitelist : tuple|Any
        # From_Value_Type_Blacklist : tuple = tuple()

        # To_Value_Type_Whitelist   : tuple|Any
        # To_Value_Type_Blacklist   : tuple = tuple()
            #Works via checking Value_Type
            #Whitelist is opertunistic (any-in:allow), blacklist is pesimistic (any-in:disalllow)

        # Value_Strict  : bool = True
        # def Value_Verify(self,value):
        #     #TODO
        #     return True 

        user_value    : Any|_unset = _unset
        value_default : Any|_unset = _unset
        _value        : Any|_unset = _unset

            #was  is giving me horrendus headaches with error traces
        @property
        def value(self):
            ''' Simplifying interface '''
            return self.value_get()

        def value_get(self):
            if self.dir in ['in','side']:
                return self.get_in_value()
            else: #self.dir in ['out']:
                return self.get_out_value()
            
        def get_out_value(self):
            for attr in self.Out_Value_Resolution_Chain:
                val = getattr(self,attr,_unset)
                if isinstance(val,(FunctionType, MethodType)):
                    val = val()
                if val is not _unset:
                    print('Get_Out_Value:', val)
                    return val
            raise Exception(f'ERROR {self} value could not resolve via Out_Value_Resolution_Chain!!')
 
        def get_in_value(self):
            for attr in self.In_Value_Resolution_Chain:
                val = getattr(self,attr,_unset)
                if isinstance(val,(FunctionType, MethodType)):
                    val = val()
                if val is not _unset:
                    print('Get_In_Value:', val)
                    return val
            raise Exception(f'ERROR  {self} value could not resolve via In_Value_Resolution_Chain!!')

        
        @value.setter
        def value(self,value):
            return self.value_set(value)
        def value_set(self,value):
            if self.dir in ['in','side']:
                return self.set_in_value(value)
            else: #self.dir in ['out']:
                return self.set_out_value(value)            
        def set_out_value(self,value):
            self._value = value
            return value
        def set_in_value(self,value):
            self.user_value = value
            return value

        # @property
        def in_graph_value_getter(self):
            ''' Graph value getter on input, uses Shape_Value.get for resolving shape of unput. May return None'''
            val = self.Value_Shape.get(self)
            print(self,'Graph Getter Value:', val)
            return val 
        
        # @property
        def out_graph_value_getter_errorless(self):
            ''' Execute/Compile without error if no values (use in defaultvalue-resolution chains) '''
            # print('out_graph_value_getter ERRORLESS CALLED')
            if self._value is _unset:
                n  = self.context.node
                fn = self.context.node.Call_Func_Name
                func = getattr(n, fn,lambda: print(f'NO FUNC FOUND OF {n}.{fn}'))
                func()

            return self._value
        
        # @property
        def out_graph_value_getter(self):
            ''' Execute/Compile with errors if no values '''

            val = self.out_graph_value_getter_errorless()
            if val is _unset:
                raise Exception(f'ERROR {self} is unset after nodes execution!!!')

            return val


    class node_mixin(_mixin.node):
        Call_Func_Name  : str = 'execute'

        #TODO: Attributes for caching
        # Deterministic   : bool
        #     # Any calls directly to this node will be re-run
        #     # Invalidates disc cachable ie Is not sharable
        #     # non-Determ is memo'd at evaluation in the context of the reader/executer (socket)
        # Result_Deterministic : bool = True
        #     #Refers to the assumption if a resulting function is deterministic or not

        # Mem_Cachable    : bool #= True
        # Disc_Cachable   : bool #= True
        #     # Values to invalidate disc/mem cachable inherited from the output sockets
        #     # Check against all output sockets being disc cachable to verify. Otherwise throw an error.

        # disc_cached   : bool = False
        # disc_location : str
        #     #wrapper will utilize this

    class exec_node_mixin(_mixin.exec_node):
        Call_Func_Name  : str = 'execute'
        def execute(): raise Exception('UNSET')

    class placeholder_node_mixin(_mixin.exec_placeholder_node):
        Call_Func_Name  : str = 'execute'
        def execute(): raise Exception('UNSET')
        
    class meta_node_mixin(_mixin.meta_node):
        Call_Func_Name  : str = 'compile'
        def compile(): raise Exception('UNSET')

