from .Data_Structures           import Backwards_Context
from ..Execution_Types          import item, _mixin, socket_shapes
from ..utils.print_debug        import debug_print_wrapper
from ...statics                 import _unset
from ...models.struct_hook_base import hook, hook_trigger
from ...models.struct_module    import module_test
from ...models.base_node        import (subgraph            as _subgraph_base,
                                        node_collection     as _node_collection_base,
                                        subgraph_collection as _subgraph_collection_base,
                                        socket_group)


from typing import Any
from contextvars import ContextVar
from contextlib  import contextmanager

class exec_test_int_socket(item.socket):
    ''' Hold, return '''
    Module        = None #SET THIS LATER 
    UID           = '_TestExecSocket'
    Version       = '1.0'
    Value_Type    = int
    Value_Default = _unset

class exec_test_add_node(item.exec_node):
    ''' Add two input sockets '''
    Module  = None #SET THIS LATER 
    UID     = '_TestExecNode'

    Version = '1.0'

    test_module_executed = False

    # in_sockets   = [exec_test_int_socket,
    #                 exec_test_int_socket]
    # out_sockets  = [exec_test_int_socket]

    in_sockets   = [socket_group.construct('set_a', Sockets=[exec_test_int_socket]),
                    socket_group.construct('set_b', Sockets=[exec_test_int_socket])]
    out_sockets  = [socket_group.construct('set_a', Sockets=[exec_test_int_socket])]


    @hook_trigger('execute')        #REQUIRED
    def execute(self)->None:
        i1 = self.in_sockets[0].execute()
        i2 = self.in_sockets[1].execute()
        val = i1 + i2
        self.out_sockets[0].value = val
        return val

_test_items_ = [
    exec_test_int_socket,
    exec_test_add_node,
]