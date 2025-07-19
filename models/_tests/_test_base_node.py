from ..base_node import pointer_socket

def test_context_socketpointer():
    assert(pointer_socket().context.root_graph is None)

from ..base_node import socket
def test_context_socket_socketPointer():
    ns = socket()
    sp = pointer_socket()
    ns.out_links = [sp]

    