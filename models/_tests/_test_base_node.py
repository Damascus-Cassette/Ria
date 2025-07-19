from ..base_node import pointer_socket
from pytest import fixture

@fixture
def struct()->tuple:
    from ..base_node import pointer_socket,socket,socket_group,node

    class _socket(socket):
        Value_Type    = str
        Default_ID    = 'Test_Socket'
        Default_Label = 'Test_Socket'

    class _node(node):
        in_sockets   = [_socket]
        out_sockets  = [_socket]
        side_sockets = [_socket]

    return _socket,_node

def test_context_socketpointer():
    assert(pointer_socket().context.root_graph is None)

from ..base_node import socket
def test_context_socket_socketPointer():
    ns = socket()
    sp = pointer_socket()
    ns.out_links = [sp]

    ns._context_walk_()
    assert sp.context.socket == ns

def test_context_node_through_pointer(struct):
    socket,node,*other = struct
    _node = node()
    _node.default_sockets()
    _node._context_walk_()
    list(_node.in_sockets.items())[0].context.node = _node