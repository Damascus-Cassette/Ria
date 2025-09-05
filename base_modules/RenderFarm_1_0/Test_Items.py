
from ..Execution_Types          import item, _mixin, socket_shapes
from ..utils.print_debug        import debug_print_wrapper, debug_print as dprint
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
    
class meta_test_socket(item.socket):
    ''' Hold, return '''
    Module        = None #SET THIS LATER 
    UID           = '_TestMetaSocket'
    Version       = '1.0'
    Value_Type    = item.socket|int
    Default_Value = 0
    ...    

class meta_test_add_node(item.meta_node):
    ''' Add two input sockets '''
    Module  = None #SET THIS LATER 
    UID     = '_TestMetaNode'

    Version = '1.0'

    test_module_executed = False

    in_sockets   = [socket_group.construct('set_a', Sockets=[meta_test_socket]),
                    socket_group.construct('set_b', Sockets=[meta_test_socket])]
    out_sockets  = [socket_group.construct('set_a', Sockets=[meta_test_socket])]


    @hook_trigger('compile')        #REQUIRED
    @debug_print_wrapper(0)
    def compile(self, exec_graph, backwards_context, state_key)->None:
        print ('STATE KEY:',self.current_context_state_key.get())

        i1 = self.in_sockets[0].compile(exec_graph, backwards_context)
        i2 = self.in_sockets[1].compile(exec_graph, backwards_context)
        #Should be unset, a value or sockets
        # print(exec_graph)
        # i2 = self.in_sockets[1].compile()
            #Want to have this pickup the passed in args automatically. Decreases friction
        
        # with exec_graph.As_Env(auto_add_nodes = True, auto_add_links = True):
        with exec_graph.As_Env(auto_add_nodes = True, auto_add_links = True):
            length= len(exec_graph.nodes)
            val = exec_test_add_node.M(i1,i2)
            dprint(i1,i2, threshold=0)
            assert len(exec_graph.nodes) == length + 1
            #Looks to be spawning extra nodes??
        self.out_sockets[0].value = val.out_sockets[0]

        assert len(exec_graph.nodes) == length + 1  

        return val

_test_items_ = [
    exec_test_int_socket,
    exec_test_add_node,
    meta_test_socket,
    meta_test_add_node,
]