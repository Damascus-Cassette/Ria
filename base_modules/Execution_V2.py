''' A bundle of Execution modules that sorts features into individual modules for current cognitive simplicity '''

from ..models.struct_module import module
from .Execution_Types import _mixin, item
from .utils.statics   import get_data_uuid, get_file_uid, INVALID_UUID
from contextvars      import ContextVar
from typing import Any
walk_force = ContextVar('walk_force',default=False)

# class deterministic_chain():
#     ''' If self & all walking upstream are deterministic, and thus walk_hash is valid to use. '''
#     class socket_mixin(_mixin.socket):
#         Deterministic : bool = True

#         @property
#         def deterministic_chain(self)->bool:
#             all_determ = []

#             if self.dir in ['in','side']:
#                 all_determ.append(self.Deterministic)
#                 for x in self.links:
#                     all_determ.append(x.in_socket.deterministic_chain)
                    
#             elif self.dir in ['out']:
#                 all_determ.append(self.context.node.deterministic_chain)

#             else: 
#                 raise Exception('DIRECTION NOT FOUND: ', self.dir)

#             return all(all_determ)

#     class exec_node_mixin(_mixin.exec_node):
#         Determininistic : bool
        
#         @property
#         def deterministic_chain(self)->bool:
#             all_determ = []
#             all_determ.append(self.Deterministic)
#             for v in self.in_sockets:
#                 all_determ.append(v.deterministic_chain)
#             for v in self.side_sockets:
#                 all_determ.append(v.deterministic_chain) 
#             return all(all_determ)



# class walk_hash():
#     ''' Walk hash, traverse tree to get hashsum of used values used as keys for caches
#     non-default implimentations may benefit the return as a list of keys 
#     '''

#     class socket_mixin(_mixin.socket):
#         _socket_out_is_src_ : bool = False
#             #Calls value on socket instead of node.
#             #Edge case

#         value_hash : property

#         @property
#         def walk_hash(self)->list[str]:
#             _hash = ''

#             if self.dir in ['in','side']:
#                 links = [x for x in self.links]
#                 if len(links):
#                     for x in links:
#                         _hash += x.in_socket.walk_hash
#                 else:
#                     self.value_hash()
            
#             elif self.dir in ['out'] and not self._socket_out_is_src_:
#                 _hash += self.context.node.walk_hash
#             elif self.dir in ['out'] and self._socket_out_is_src_:
#                 _hash += self.value_hash()
#             else: 
#                 raise Exception('DIRECTION NOT FOUND: ', self.dir)
            
#             return [get_data_uuid(walk_hash)]
        
#     class node_mixin(_mixin.exec_node):
#         @property
#         def walk_hash(self)->list[str]:
#             for v in self.in_sockets:
#                 _hash =+ v.walk_hash
#             for v in self.side_sockets:
#                 _hash =+ v.walk_hash 
#             return [get_data_uuid(_hash)]
    

# class value_hash():
#     ''' Localized value hash, invalid if not all inputs are executed (thus could be shorthand, though may be bad practice) '''

#     class node_mixin(_mixin.exec_node):
#         _node_local_values_ : list[str] = []

#         @property
#         def value_hash(self)->list[str]:
#             _pre_sum = []
#             for k in self._node_local_values_:
#                 v = getattr(self,k,None)
#                 if hasattr(v,'value_hash'):
#                     _pre_sum.append (v.value_hash)
#                 else:
#                     _pre_sum.append(get_data_uuid(v))

#             for v in self.in_sockets:
#                 _pre_sum.append (v.value_hash)
#             for v in self.side_sockets:
#                 _pre_sum.append (v.value_hash)

#             if INVALID_UUID in _pre_sum: 
#                 return INVALID_UUID

#             return [get_data_uuid(''.join(_pre_sum))]

#     class socket_mixin():
#         executed    : bool = False
#         _value_hash : str

#         @property
#         def value_hash(self)->str:
#             _pre_sum = []
#             if self.dir in ['in','side']:
#                 links = [x for x in self.links]
#                 if len(links):
#                     for x in links:
#                         if x.executed:
#                             _pre_sum.append(x.in_socket.value_hash)
#                         else:
#                             _pre_sum.append(INVALID_UUID)
#                 else:
#                     _hash = self.get_local_value_hash()
#                     if _hash != INVALID_UUID:
#                         self._value_hash = _hash
#                     return _hash
                
#             elif self.dir in ['out']:
#                 _pre_sum.append(self.get_local_value_hash())

#             else: 
#                 raise Exception('DIRECTION NOT FOUND: ', self.dir)
            
#             if INVALID_UUID in _pre_sum:
#                 return INVALID_UUID
            
#             ret = self._value_hash = get_data_uuid(''.join(_pre_sum))
#             return ret

#         #The namespace & methodology of this module feels somewhat fragile, or rather; not structural
        
#         def get_local_value_hash(self)->str:
#             a = getattr(self,'data',None)
#             if hasattr(a,'value_hash'):
#                 return a.value_hash
#             else:
#                 get_data_uuid(a)


# class _node_execution():
#     def __init__(self,func):
#         self.func = func
#     def __get__(self, obj, objtype):
#         return functools.partial(self.__call__, obj)
    
#     def __call__(self,container:_mixin.exec_node,*args,**kwargs):
#         #fullfills and staches caches based on exeuction.
#         #Depending on mode it could be simpler
#         # container.Deterministic
#         return self.func(container,*args,**kwargs)

# def node_exectution(func):
#     ''' Will expand later to include args such as contextual cache invalidation'''
#     return _node_execution(func)

from types import UnionType, FunctionType
from inspect import isclass
class _unset():...

context = ContextVar('execution context', default=defaultDict(default=None))


from .Execution_V2_type_containers import (locked_data_container,
                                           locked_func_container,
                                           locked_prop_container,
                                           unlocked_func_container)

class socket_shapes():
    class mutable[T]():
        def get(cls,socket)->list[T]|T|_unset:
            if socket.Links_Max > 1:
                res = []
                for x in socket.links: 
                    res.append(cls.Resolve(x.out_socket.value))
                if res:
                    return res
                else:
                    return _unset
                
            else:
                if len(socket.links):
                    return socket.links[0].out_socket.value
                else:
                    return _unset

    class single[T]():
        @classmethod
        def get(cls,socket)->T|_unset:
            ''' Calls upstream socket.value and returns it. 
            Resolves FunctionType|context_function w/a.
            Base is any input formatted, no resolution of functions 
            _unset is returned to allow for fallback values
            '''
            if len(socket.links) > 0:
                ...
            else:
                return _unset

        def Resolve[T](value:T)->T:
            return value

    class multi[T]():
        @classmethod
        def get(cls,socket)->list[T]|_unset:
            ''' Calls upstream [socket.value] and returns it '''
            res = []
            for x in socket.links: 
                res.append(cls.Resolve(x.out_socket.value))
            if res:
                return res
            else:
                return _unset
        
        def Resolve[T](value:T)->T:
            return value

    class c_func(single):
        def Resolve[T](value:T)->T:
            # if isclass(value):
            #     return value
            if not isinstance(value,(FunctionType,context_function)):
                value = lambda *args, **kwargs: value
            return value
    
    class c_funcs(multi):
        def Resolve[T](value:T)->T:
            if not isinstance(value,(FunctionType,context_function)):
                value = lambda *args, **kwargs: value
            return value

    
    class value(single):
        ''' Collapsing to a value on a socket automatically can throw errors with missing arguments. Be aware! '''
        def Resolve[T](value:T)->T:
            if isinstance(value,(FunctionType,context_function)):
                value = value()
            return value
        
    class values(multi):
        def Resolve[T](value:T)->T:
            if isinstance(value,(FunctionType,context_function)):
                value = value()
            return value

    _single = [c_func ,value ]
    _multi  = [c_funcs,values]

st = socket_shapes

class main(module):
    UID          = 'Core_Execution'
    Label        = 'Core_Execution'
    Desc         = ''' Core execution method  '''
    ChangeLog    = ''' '''
    Version      = '2.0'

    class socket_mixin(_mixin.socket):
        
        Value_Shape   : st.single|st.multi
            #Statement to make inputs typed single or multi
        Value_Type    : Any|set[Any]|UnionType
            #Statemnt of type(s) produced by socket.
        Value_Default : Any = _unset
            #Not saved to file.
            
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
                if issubclass(ty,(st.single,st.multi,st.mutable)):
                    cls.Value_Shape = ty.__origin__
                    cls.Value_Type  = set[ty.__args__]
                elif issubclass(ty,UnionType):
                    cls.Value_Type  = set[ty.__args__]
            else:
                assert isinstance(ty,(list,set,tuple))

            if not hasattr(getattr(cls,'Value_Shape',_unset),'get'):
                cls.Value_Shape = st.mutable

            super().__init_subclass__()

            
        In_Value_Resolution_Chain  = {'value_graph','user_value','value_default','Value_Default'}
        Out_Value_Resolution_Chain = {'value_graph'}
            #these could be a property for custom things that connect to UI

        @property
        def value(self):
            if self.Direction in ['in','side']:
                attr_chain = self.In_Value_Resolution_Chain
            else:
                attr_chain = self.Out_Value_Resolution_Chain

            for attr in attr_chain:
                if val:=getattr(self,attr) is not _unset:
                    return val
            return _unset
            
        # In_Value_Set  : list|str = ['_value']
        # Out_Value_Set : list|str = ['_value']
        # @value.setter
        # def value(self,value):
        #     ''' Set Via Set chains? May just not allow to be setable '''
        # Could set Exec_Value on out, raise error on in

        _value_exec    : any = _unset  
        _value_graph   : any = _unset
        _value_user    : any = _unset
        value_default  : any = _unset
            #socket Inst  value default
            #TODO: ay need to be typed differently to save correctly

        @property
        def value_user(self):
            return self._value_user 
        @value_user.setter
        def value_user(self,value):
            self._value_user = value 
            
            #From the node itself
            #Only set if mem-cachable & Deterministic
        @property
        def value_exec(self):
            ''' Property that can only be accessed on the '''
            assert self.Direction == 'out'
            return getattr(self,'_value_exec',_unset)
        @value_exec.setter
        def value_exec(self,value):
            assert self.Direction == 'out'
            self._value_exec = value

        @property
        def value_graph(self):
            ''' Auto execution property '''
            if self.Direction in ['in','side']:
                return self.Value_Shape.get(self)
            else:
                val = self.value_exec
                if val is _unset:
                    self.context.node.execute()
                val = self.value_exec
                if val is _unset:
                    raise Exception('SOCKET value_exec WAS NOT SET DURING EXECUTION')
                return val


    class node_mixin(_mixin.node):
        Value_Type  : Any       = Any
        Value_Allow : list[Any] = [Any]
            # Fallback values from socket_group.

        Deterministic   : bool
            #Invalidates mem|disc cachable
                #Is not sharable
            #Any calls directly to this node will be re-run

        Mem_Cachable    : bool #= True
        Disc_Cachable   : bool #= True
            # If this socket can be cached to disc or not
            # If false, invalidates disc_cachable on exec_node
            # Check against all sockets being disc/mem cachable

        #### Constructed Methods & Vars ####
        Call_Cache_Dump : bool = False
        Call_Cache_Load : bool = False

        def Cache_Dump(self,dir):
            ''' Dump cache infor to location w/a, set disc_loc and disc_cached for cache_load'''
        def Cache_Load(self):
            ''' Load cache from disc_loc, set to self.value '''
        
        disc_cached   : bool = False
        disc_location : str


    class exec_node_mixin(_mixin.exec_node):
        def execute(self):
            ''' Exeuction Function '''
            raise Exception(f'Execution has not been defined on {self.UID} of ({self.module.UID} : {self.module.Version}) !')

        def execute_inputs(self,):
            ''' Calls execute on all inputs '''
            for x in self.in_sockets:
                ...


    class placeholder_node_mixin(_mixin.exec_placeholder_node):
        def execute(): ...
        
    class meta_node_mixin(_mixin.meta_node):
        def compile(): ...

