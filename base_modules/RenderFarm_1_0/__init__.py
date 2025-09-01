from ...models.struct_module    import module
from ..utils.print_debug import (debug_print_wrapper as dp_wrap, 
                                 _debug_print        as dprint )

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
            - True random output, single time execution 
            - Externally declared values
            - User inputs (Cache-intercept)
        - Checkpoints & Breakpoints
            - Branching and diffing
    '''

    UID     = 'Distributed_Execution'
    Version = '1.0'
    Dependencies = [
        ('Monadish','=1.2')
    ]

from .Submodule_ExecFlow import _exec_flow_mixins_, _exec_flow_items_, _execflow_test_
for x in _exec_flow_items_: x.Module = main
_execflow_test_.module               = main

main._loader_mixins_.extend(_exec_flow_mixins_)
main._loader_items_ .extend(_exec_flow_items_ )
main._module_tests_ .append(_execflow_test_   )
    #A Submodule loader would be a nice little util to clean this up