from ...models.struct_module    import module, module_test
from ...models.base_node        import socket_group, node_set_base
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



######## MIXINS ########
# region

class graph_mixin(_mixin.graph):
    ''' Contain job datastructure & session context/allowences '''

class socket_mixin(_mixin.socket):
    ''' '''

class node_mixin(_mixin.node):
    ''' Declaring Execution_Caching Setting for later use '''

    Deterministic      : bool
    Mem_Cachable       : bool
    Disc_Cachable      : bool

    Cache_Check_Server : bool

main._loader_mixins_ = [
    graph_mixin  ,
    node_mixin   ,
    socket_mixin ,
]

#endregion


######## BUILT IN NODES ######## 

class compile_placeholder(item.exec_node):
    ''' Placeholder in execution, to re-trigger compile with a stored context toward a specific node 
    This allows defering compilation that depends on un-executed variables.
    '''

    UID = 'EXEC_compile_placeholder'
    Version = '1.0'

    in_sockets  = []
    out_sockets = []

    target_node     : item.meta_node
    cached_context  : dict|BaseModel
        # Potential problem: Storing reference across graphs. 
        # May have to hack it and store the graph & node ID.

    def execute(self, context, subgraph):
        ''' Call target node to compile '''
        ...

    @classmethod
    def create(cls,node)->Self:
        ''' Format toward the incoming node and store a copy of the context locally
        Should be 1 to 1 with the incoming node's sockets.
        ''' #Consider using copy and _context_walk_ manually to graft onto this object?
        ... 


######## TEST NODES ########
# region

class node_exec_example(item.exec_node):
    UID     = 'EXEC_add'
    Version = '1.0'

    in_sockets  = []
    out_sockets = []

    # @hook_trigger('execute') #Should be Auto Wrapped
    def execute(self, context, subgraph, session):
        ...

class node_meta_example(item.meta_node):
    UID     = 'META_add'
    Version = '1.0'
    
    in_sockets  = []
    out_sockets = []
    
    # @hook_trigger('compile') #Should be Auto Wrapped
    def compile(self, context, subgraph):
        ...


class repeat_zone_meta(node_set_base):
    ''' Node set that compiles'''

    class zone_start(item.meta_node):
        UID = 'META_repeat_zone_start'
        Version = '1.0'

        in_sockets  = []
        out_sockets = []

        def compile(self, context, subgraph):
            ...

    class zone_end(item.meta_node):
        UID = 'META_repeat_zone_end'
        Version = '1.0'

        in_sockets  = []
        out_sockets = []

        def compile(self, context, subgraph):
            ...
        
class multi_zone_meta(node_set_base):
    ''' Threading compilation'''

    class zone_start(item.meta_node):
        UID = 'META_multi_zone_start'
        Version = '1.0'

        in_sockets  = []
        out_sockets = []

        def compile(self, context, subgraph):
            ...

    class zone_end(item.meta_node):
        UID = 'META_multi_zone_end'
        Version = '1.0'

        in_sockets  = []
        out_sockets = []

        def compile(self, context, subgraph):
            ...

main._loader_items_ = [
    node_exec_example,
    node_meta_example,
    *repeat_zone_meta.Nodes_Types,
    *multi_zone_meta.Nodes_Types,
]

#endregion



######## TESTS ########
#region

def test_exec(graph,subgraph):
    ...

def test_compile(graph,subgraph):
    ...

def test_zone_repeat_compile(graph,subgraph):
    ...

def test_zone_multi_compile(graph,subgraph):
    ...

def test_placeholder_creation(graph,subgraph):
    ...

def test_placeholder_execution(graph,subgraph):
    ...

# def test_task():
#     ...

main._module_tests_.append(
    module_test('TestA',
        module      = main,
        funcs       = [
            test_exec,
            test_compile,
            test_zone_repeat_compile,
            test_zone_multi_compile,
            test_placeholder_creation,
            test_placeholder_execution,
        ],
        module_iten = {main.UID : main.Version,
                      'Monadish':'1.2'}, 
        ))


#endregion