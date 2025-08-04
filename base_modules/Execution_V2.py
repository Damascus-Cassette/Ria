''' A bundle of Execution modules that sorts features into individual modules for current cognitive simplicity '''

from ..models.struct_module import module
from .Execution_Types import _mixin, item, statics
from .utils.statics   import get_data_uuid, get_file_uid
from contextvars      import ContextVar

walk_force = ContextVar(default=False)

class deterministic_chain():
    ''' If self & all walking upstream are deterministic, and thus walk_hash is valid to use. '''
    class socket_mixin(_mixin.socket):
        Deterministic : bool = True

        @property
        def deterministic_chain(self)->bool:
            all_determ = []

            if self.dir in ['in','side']:
                all_determ.append(self.Deterministic)
                for x in self.links:
                    all_determ.append(x.in_socket.deterministic_chain)
                    
            elif self.dir in ['out']:
                all_determ.append(self.context.node.deterministic_chain)

            else: 
                raise Exception('DIRECTION NOT FOUND: ', self.dir)

            return all(all_determ)

    class exec_node_mixin(_mixin.exec_node):
        Determininistic : bool
        
        @property
        def deterministic_chain(self)->bool:
            all_determ = []
            all_determ.append(self.Deterministic)
            for v in self.in_sockets:
                all_determ.append(v.deterministic_chain)
            for v in self.side_sockets:
                all_determ.append(v.deterministic_chain) 
            return all(all_determ)



class walk_hash():
    ''' Walk hash, traverse tree to get hashsum of used values used as keys for caches
    non-default implimentations may benefit the return as a list of keys 
    '''

    class socket_mixin(_mixin.socket):
        _socket_out_is_src_ : bool = False
            #Calls value on socket instead of node.
            #Edge case

        value_hash : property[str]

        @property
        def walk_hash(self)->list[str]:
            _hash = ''

            if self.dir in ['in','side']:
                links = [x for x in self.links]
                if len(links):
                    for x in links:
                        _hash += x.in_socket.walk_hash
                else:
                    self.value_hash()
            
            elif self.dir in ['out'] and not self._socket_out_is_src_:
                _hash += self.context.node.walk_hash
            elif self.dir in ['out'] and self._socket_out_is_src_:
                _hash += self.value_hash()
            else: 
                raise Exception('DIRECTION NOT FOUND: ', self.dir)
            
            return [get_data_uuid(walk_hash)]
        
    class node_mixin(_mixin.exec_node):
        @property
        def walk_hash(self)->list[str]:
            for v in self.in_sockets:
                _hash =+ v.walk_hash
            for v in self.side_sockets:
                _hash =+ v.walk_hash 
            return [get_data_uuid(_hash)]
    

class value_hash():
    ''' Localized value hash, invalid if not all inputs are executed (thus could be shorthand, though may be bad practice) '''

    class node_mixin(_mixin.exec_node):
        _node_local_values_ : list[str] = []

        @property
        def value_hash(self)->list[str]:
            _pre_sum = []
            for k in self._node_local_values_:
                v = getattr(self,k,None)
                if hasattr(v,'value_hash'):
                    _pre_sum.append (v.value_hash)
                else:
                    _pre_sum.append(get_data_uuid(v))

            for v in self.in_sockets:
                _pre_sum.append (v.value_hash)
            for v in self.side_sockets:
                _pre_sum.append (v.value_hash)

            if statics.INVALID_UUID in _pre_sum: 
                return statics.INVALID_UUID

            return [get_data_uuid(''.join(_pre_sum))]

    class socket_mixin():
        executed    : bool = False
        _value_hash : str

        @property
        def value_hash(self)->str:
            _pre_sum = []
            if self.dir in ['in','side']:
                links = [x for x in self.links]
                if len(links):
                    for x in links:
                        if x.executed:
                            _pre_sum.append(x.in_socket.value_hash)
                        else:
                            _pre_sum.append(statics.INVALID_UUID)
                else:
                    _hash = self.get_local_value_hash()
                    if _hash != statics.INVALID_UUID:
                        self._value_hash = _hash
                    return _hash
                
            elif self.dir in ['out']:
                _pre_sum.append(self.get_local_value_hash())

            else: 
                raise Exception('DIRECTION NOT FOUND: ', self.dir)
            
            if statics.INVALID_UUID in _pre_sum:
                return statics.INVALID_UUID
            
            ret = self._value_hash = get_data_uuid(''.join(_pre_sum))
            return ret

        #The namespace & methodology of this module feels somewhat fragile, or rather; not structural
        
        def get_local_value_hash(self)->str:
            a = getattr(self,'data',None)
            if hasattr(a,'value_hash'):
                return a.value_hash
            else:
                get_data_uuid(a)

from contextlib import contextmanager


import functools

class _node_execution():
    def __init__(self,func):
        self.func = func
    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)
    
    def __call__(self,container:_mixin.exec_node,*args,**kwargs):
        #fullfills and staches caches based on exeuction.
        #Depending on mode it could be simpler
        # container.Deterministic
        return self.func(container,*args,**kwargs)

def node_exectution(func):
    ''' Will expand later to include args such as contextual cache invalidation'''
    return _node_execution(func)


class main(module):
    UID          = 'Core_Execution'
    Label        = 'Core_Execution'
    Desc         = ''' Core execution method  '''
    ChangeLog    = ''' '''
    Version      = '1.0'
    class exec_node_mixin(_mixin.exec_node):
        #### Properties ####

        #### Execution Logic ####

        @node_exectution
        def execute(self):
            ''' Exeuction Function '''
            raise Exception(f'Execution has not been defined on {self.UID} of ({self.module.UID} : {self.module.Version}) !')

        def execute_inputs(self,):
            ''' Calls execute on all inputs '''
            for x in self.in_sockets:
                

        #### Properties ####


    class placeholder_node_mixin(_mixin.exec_placeholder_node):
        def execute(): ...
        
    class meta_node_mixin(_mixin.meta_node):
        def compile(): ...

