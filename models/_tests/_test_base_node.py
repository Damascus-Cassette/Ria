from pytest import fixture

from ..base_node import socket,node
@fixture
def node_struct()->tuple:

    class _socket(socket):
        Value_Type    = str
        Default_ID    = 'Test_Socket'
        Default_Label = 'Test_Socket'

    class _node(node):
        in_sockets   = [_socket,_socket]
        out_sockets  = [_socket]
        side_sockets = [_socket]

    return _socket,_node

from ..base_node import subgraph
from ..base_node import graph

@fixture
def graph_def():
    inst = graph()
    inst.label = 'Test_Graph'
    inst.subgraphs.new()

@fixture
def node_def(node_struct):
    socket,node,*other = node_struct
    _node = node()
    _node.default_sockets()
    _node._context_walk_() 
    return _node

def test_context_socketpointer():
    assert(node().context.root_graph is None)

from ..base_node import socket
def test_context_socket_socketPointer():
    ns = socket()
    sp = pointer_socket()
    ns.out_links = [sp]

    ns._context_walk_()
    assert sp.context.socket == ns

def test_context_node_through_pointer(node_def):
    list(node_def.in_sockets.values())[0].context.node = node_def
    
def test_struct_node(node_def):
    assert len(node_def.in_sockets.items())   == 2
    assert len(node_def.out_sockets.items())  == 1
    assert len(node_def.side_sockets.items()) == 1
    