''' A bundle of Execution modules that sorts features into individual modules for current cognitive simplicity '''

from .utils.statics         import get_data_uuid, get_file_uid, INVALID_UUID
from .Execution_Types       import _mixin, item
from ..statics              import _unset
from ..models.struct_module import module
from .Execution_Types       import socket_shapes as st

from typing           import Any, Self, get_type_hints, ForwardRef, TypeAlias
from types            import UnionType, FunctionType
from collections      import defaultdict
from contextvars      import ContextVar
from inspect          import isclass


context = ContextVar('execution context', default=defaultdict(default=None))

fwd_ref : TypeAlias = 'unlocked_func_container'

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

    def __init__[R=Any,F=FunctionType](self, src_node, func:F, return_type:R=Any, f_id=''): #->unlocked_func_container[F,R]
        self : Self[R,F]
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





class main(module):
    UID          = 'Core_Execution'
    Label        = 'Core_Execution'
    Desc         = ''' Core execution method  '''
    ChangeLog    = ''' '''
    Version      = '2.0'

    class socket_mixin(_mixin.socket):
        #### Constructed Methods & Vars ####
        Value_Shape   : st.mutable = st.mutable # Statement to make assert shapes/forms                                                
        Value_Type    : Any|set[Any]|UnionType  # Statemnt of type(s) produced by socket.
        Value_Default : Any = _unset            # Not saved to file.

        In_Value_Resolution_Chain  = {'in_graph_value_getter' ,'user_value','value_default','Value_Default'}
        Out_Value_Resolution_Chain = {'out_graph_value_getter'} 
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
        # From_Value_Type_Whitelist : set|Any
        # From_Value_Type_Blacklist : set = set()

        # To_Value_Type_Whitelist   : set|Any
        # To_Value_Type_Blacklist   : set = set()
            #Works via checking Value_Type
            #Whitelist is opertunistic (any-in:allow), blacklist is pesimistic (any-in:disalllow)

        # Value_Strict  : bool = True
        # def Value_Verify(self,value):
        #     #TODO
        #     return True 

        user_value    : Any = _unset
        value_default : Any = _unset

        @property
        def value(self):
            ''' Simplifying interface '''
            return self.get_value()

        def get_value(self):
            if self.Direction in ['in','side']:
                return self.get_in_value()
            else: #self.Direction in ['out']:
                return self.get_out_value()
            
        def get_out_value(self):
            for attr in self.In_Value_Resolution_Chain:
                if val:=getattr(self,attr,_unset) is not _unset:
                    return val
            raise Exception(f'ERROR Socket {self} could not resolve via In_Value_Resolution_Chain!!')
        def get_in_value(self):
            for attr in self.In_Value_Resolution_Chain:
                if val:=getattr(self,attr,_unset) is not _unset:
                    return val
            raise Exception(f'ERROR Socket {self} could not resolve via In_Value_Resolution_Chain!!')

        @value.setter
        def value_setter(self,value):
            ''' Simplifying interface '''
            assert self.Direction in ['out']
            self.set_value(value)
        def set_value(self,value):
            self._value = value

        @property
        def in_graph_value_getter(self):
            ''' Graph value getter on input, uses Shape_Value.get for resolving shape of unput. May return None'''
            return self.Value_Shape.get()

        @property
        def out_graph_value_getter_errorless(self):
            ''' Execute/Compile without error if no values (use in defaultvalue-resolution chains) '''
            if self._value is _unset:
                getattr(self.context.node,self.context.node.Call_Func_Name)()
            return self._value
        
        @property
        def out_graph_value_getter(self):
            ''' Execute/Compile with errors if no values '''
            if val:=self.out_graph_value_getter_errorless is _unset:
                raise Exception(f'ERROR Socket {self} is unset after nodes execution!!!')
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

