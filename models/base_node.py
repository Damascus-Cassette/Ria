from typing import Any, Self

class pointer_socket():
    node      : node
    socket_id : str

class socket():
    set_id : str
    value  : Any

class socket_set():
    sockets : dict[socket]

class socket_collection():
    ...

class node():
    ...


if __name__ == '__main__':

    class socket_type(socket):
        ...

    class test_node(node):
        ...