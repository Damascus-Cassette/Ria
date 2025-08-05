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
    #TODO: Add facotry methods!
    
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


