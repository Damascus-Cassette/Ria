from ..models.struct_module import module
from .Execution_Types import _mixin, item, statics
from .utils.statics   import get_data_uuid, get_file_uid
from contextvars      import ContextVar

walk_force = ContextVar(default=False)

class main_hash(module):
    class socket_mixin(_mixin.socket):
        _io_blacklist_ = ['_walk_sum']
        
        Deterministic       : bool = True
        chain_deterministic : bool
        _walk_sum           : str

        def walk(self)-> tuple[str,bool]:
            if walk_force.get() and hasattr(self,'chain_deterministic') and hasattr(self,'_walk_sum'):
                return self._walk_sum, self.chain_deterministic
            elif self.dir in ['in','side']:
                return self.in_walk()
            elif self.dir in ['out']:
                return self.side_walk()
            raise Exception(f'DIRECTION NOT FOUND! {self.dir}')

        def in_walk(self)-> tuple[str,bool]:
            ''' Returns socket's walk value and if it's deterministic or not (! node deterministic invalidates return) '''
            
            _hash = ''
            determ   = True

            for k,v in self.links:
                _h, _d  = v.out_socket.out_walk()
                _hash   += _h 
                _determ += _d
                if not _determ: 
                    determ = False
            
            _hash += self.value_hash
            _hash = get_data_uuid(_hash)
            self._walk_sum = _hash
            return _hash, determ
    
        def out_walk(self)-> tuple[str,bool]:
            node = self.context.node

            _hash,determ = node.walk()

            if not node.Deterministic:
                determ = False

            self._walk_sum = _hash
            return _hash,determ
        
        def value_sum(self):
            if walk_force.get() and hasattr(self,'_value_sum'):
                return self._value_sum
            assert self.dir in ['in','side']
            
            _hash = self.get_value_uuid()

            self._value_sum

    class exec_node_mixin(_mixin.exec_node):
        def walk(self):
            ''' root recursion for walking, helps determine context hash. '''
            _hash = ''
            determ = self.Deterministic
            
            for k,v in self.in_sockets.items():
                _hsh,_determ = v.in_walk()
                _hash =+ _hsh
                if not _determ: determ = False

            for k,v in self.side_sockets.items():
                _hsh,_determ = v.in_walk()
                _hash =+ _hsh
                if not _determ: determ = False

            self.chain_deterministic = determ
            self.walk_sum = get_data_uuid(_hash)

        @property
        def walk_sum(self)->str:
            ''' uuid/deterministic hashsum from inputs/sides's walk_sum
            Only called (if self.deterministic_chain)
            Lazy default to input's _walk_sum by default
            Does not allow lists for simplicity of structure. '''
            if not self.chain_deterministic:
                return []
 
            for k,v in self.in_sockets.items():
                ...
            for k,v in self.side_sockets.items():
                ...
            # ret = ''
            # #TODO
            # self._walk_sum = ret
        
        @property
        def value_sum(self)->str|list[str]:
            ''' uuid/deterministic hashsum from inputs/sides's values
            Only called (if self.Deterministic)
            Returns list of all applicable execution-uids, allows a user to have node logic dictate multiple possiblility hashes more clearly
            Say A+B+C, result could be order agnostic or internally ordered
            or res could be Gated so that C is only added if B. So 2 applicable hashes exist.   '''
            if not self.Deterministic:
                return []
            # ret = ''
            # #TODO
            # self._value_sum = ret
        
        def chain_deterministic():
            ...

class main_execution(module):
    class exec_node_mixin(_mixin.exec_node):
        #### Properties ####

        #### Execution Logic ####

        def execute_inputs(self,):
            ''' Calls execute on all inputs '''

        #### Setup Ease Functions ####

        def inherit_sockets(self,meta_node):
            ''' Inherit sockets from a meta_nodes ''' 

        def inherit_connections(self,meta_node):
            ''' Inherit exec_node connections from a meta_node ''' 


        #### Properties ####




    class placeholder_node_mixin(_mixin.exec_placeholder_node):
        def execute(): ...
        
    class meta_node_mixin(_mixin.meta_node):
        def compile(): ...

