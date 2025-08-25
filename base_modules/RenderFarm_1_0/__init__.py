from ...models.struct_module    import module, module_test
from ...models.base_node        import socket_group
from ..Execution_Types          import _mixin, item
from ...models.struct_hook_base import hook, hook_trigger
from ..utils.print_debug import (debug_print_wrapper as dp_wrap, 
                                 _debug_print        as dprint ,
                                 debug_level                   , 
                                 debug_targets                 ) 

class main(module):
    ''' Execution engine re-write for shared items between distributed & local use 
    This adds 
        - Node execution modes:
            - Compile
            - Compile Placeholders (Callback for execute)
            - Execution
        - Tasks
            - Nodes that declare them 
            - Deps
            - Abstract repr
        - Memo
            - For true random output and externally declared values
        - User inputs
        - Checkpoints & Breakpoints
            - Branching and diffing
    '''
    UID     = 'Distributed_Execution_Common'
    Version = '1.0'
    Dependencies = [
        ('Monadish','=1.2')
    ]


class graph_mixin(_mixin.graph):
    ''' Contain job datastructure & session context/allowences'''
    ...



class node_mixin(_mixin.exec_node):
    def __init_subclass__(cls):
        #auto wrap here
        super().__init_subclass__(cls)

######## TEST NODES ########
#region

class node_exec_example(item.exec_node):
    UID     = 'EXEC_add'
    Version = '1.0'

    # @hook_trigger('execute') #Should be Auto Wrapped
    def execute(self, context, subgraph, session):
        ...

class node_meta_example(item.meta_node):
    UID     = 'META_add'
    Version = '1.0'
    
    in_sockets  = []
    out_sockets = []
    
    # @hook_trigger('compile') #Should be Auto Wrapped
    def compile(self, context, subgraph, session):
        ...

#endregion