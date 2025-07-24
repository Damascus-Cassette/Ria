from .struct_module import _mixin_base, _item_base

from .base_node import node   as _node
from .base_node import socket as _socket


from .base_node import graph      as _graph
from .base_node import meta_graph as _meta_graph

from typing import Generic

# using these as generic classes provides the type hinting without the functions.
# This is desired in the mixins as they will be inheriteed onto their bases, but not the items.
# May find in testing that I need to get rid of the generic if this works?

class mixin:
    class socket[_socket](_mixin_base):...
    class node[_node](_mixin_base):...
    class graph[_graph](_mixin_base):...
    class meta_graph[_meta_graph](_mixin_base):...

class item:
    class node(_node,_item_base):...
    class socket(_socket,_item_base):...