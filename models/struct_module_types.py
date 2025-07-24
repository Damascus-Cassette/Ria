from .struct_module import _mixin_base, _item_base
from .base_node import node as _node

from typing import Generic

# using these as generic classes provides the type hinting without the functions.
# This is desired in the mixins as they will be inheriteed onto their bases, but not the items.
# May find in testing that I need to get rid of the generic if this works?

class mixin:
    class node[_node](_mixin_base):...

class item:
    class node(_node,_item_base):...