from .struct_module import _mixin_base, _item_base

from typing import Generic

from .base_node import pointer_socket      as _pointer_socket
from .base_node import socket              as _socket
from .base_node import socket_group        as _socket_group
from .base_node import socket_collection   as _socket_collection
from .base_node import node                as _node
from .base_node import node_collection     as _node_collection
from .base_node import subgraph            as _subgraph
from .base_node import subgraph_collection as _subgraph_collection
from .base_node import graph               as _graph
from .base_node import graph_collection    as _graph_collection
from .base_node import meta_graph          as _meta_graph

# using these as generic classes provides the type hinting without the functions.
# This is desired in the mixins as they will be inheriteed onto their bases, but not the items.
# May find in testing that I need to get rid of the generic if this works?

class mixin:
    class socket[T=_socket](_mixin_base):
        _constr_bases_key_ = _socket._constr_bases_key_
    class node[T=_node](_mixin_base):
        _constr_bases_key_ = _node._constr_bases_key_

class _mixin:
    ''' For internal module mixins, use in optional modules at great risk! '''
    class pointer_socket(_mixin_base):
        _constr_bases_key_ = _pointer_socket._constr_bases_key_
    class socket(_mixin_base):
        _constr_bases_key_ = _socket._constr_bases_key_
    class socket_group(_mixin_base):
        _constr_bases_key_ = _socket_group._constr_bases_key_
    class socket_collection(_mixin_base):
        _constr_bases_key_ = _socket_collection._constr_bases_key_
    class node(_mixin_base):
        _constr_bases_key_ = _node._constr_bases_key_
    class node_collection(_mixin_base):
        _constr_bases_key_ = _node_collection._constr_bases_key_
    class subgraph(_mixin_base):
        _constr_bases_key_ = _subgraph._constr_bases_key_
    class subgraph_collection(_mixin_base):
        _constr_bases_key_ = _subgraph_collection._constr_bases_key_
    class graph(_mixin_base):
        _constr_bases_key_ = _graph._constr_bases_key_
    class graph_collection(_mixin_base):
        _constr_bases_key_ = _graph_collection._constr_bases_key_
    class meta_graph(_mixin_base):
        _constr_bases_key_ = _meta_graph._constr_bases_key_


class item:
    class node(_node,_item_base):...
    class socket(_socket,_item_base):...