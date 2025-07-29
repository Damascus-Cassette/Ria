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
    

class mixin(mixin):
    class exec_node(_mixin.node):
        _constr_bases_key_ = 'node:exec_node'
    class meta_node(_mixin.node):
        _constr_bases_key_ = 'node:meta_node'
    class exec_placeholder_node(_mixin.node):
        _constr_bases_key_ = 'node:placeholder_node'

class _mixin(mixin,_mixin): ...

class item(_item):

    class exec_node(_item.node):
        _constr_bases_key_ = 'node:exec_node'


        #### User Constructed Values ####
        
        Deterministic : bool
        Disc_Cachable : bool
        Cacheable     : bool


        #### Attributes ####
                 
        # uuid : str  #Fullfilled via collection
        chain_deterministic : bool          = True
        metadata            : exec_metadata
        _walk_sum  : str #Cache for disc
        _value_sum : str|list[str]


        #### Properties ####

        @property
        def walk_sum(self)->str:
            ''' uuid/deterministic hashsum from inputs/sides's walk_sum
            Only called (if self.deterministic_chain)
            Lazy default to input's _walk_sum by default
            Does not allow lists for simplicity of structure. '''
            ret = ''
            assert self.chain_deterministic
            #TODO
            self._walk_sum = ret
            return ret
        
        @property
        def value_sum(self)->str|list[str]:
            ''' uuid/deterministic hashsum from inputs/sides's values
            Only called (if self.Deterministic)
            Returns list of all applicable execution-uids, allows a user to have node logic dictate multiple possiblility hashes more clearly
            Say A+B+C, result could be order agnostic or internally ordered
            or res could be Gated so that C is only added if B. So 2 applicable hashes exist.   '''
            assert self.Deterministic
            ret = ''
            #TODO
            self._value_sum = ret
            return ret
        
        def __init_subclass__(cls):
            assert hasattr(cls,'Deterministic')
            assert hasattr(cls,'Disc_Cachable')
            assert hasattr(cls,'Cacheable')
            return super().__init_subclass__()


        #### Execution Logic ####

        def execute(self,):
            #User overridden. May or may not execute inputs.
            ...

        def execute_inputs(self,):
            ''' Calls execute on all inputs '''

        #### Setup Ease Functions ####

        def inherit_sockets(self,meta_node):
            ''' Inherit sockets from a meta_nodes ''' 
            #TODO

        def inherit_connections(self,meta_node):
            ''' Inherit exec_node connections from a meta_node ''' 
            #TODO

    
    class meta_node(_item.node):
        _constr_bases_key_ = 'node:meta_node'
        def compile():...
        
    class exec_placeholder_node(_item.node):
        _constr_bases_key_ = 'node:placeholder_node'
        def execute():...


