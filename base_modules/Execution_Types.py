from ..models.struct_module_types import mixin,_mixin
from ..models.struct_module_types import item as _item

class mixin(mixin):
    class meta_node(_mixin.node):
        _constr_bases_key_ = 'node:meta_node'
    class exec_node(_mixin.node):
        _constr_bases_key_ = 'node:exec_node'
    class exec_placeholder_node(_mixin.node):
        _constr_bases_key_ = 'node:placeholder_node'

class _mixin(mixin,_mixin):
    ...

class item(_item):
    class meta_node(_item.node):
        _constr_bases_key_ = 'node:meta_node'
    class exec_node(_item.node):
        _constr_bases_key_ = 'node:exec_node'
    class exec_placeholder_node(_item.node):
        _constr_bases_key_ = 'node:placeholder_node'