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
            - For true random output and externally declared values
        - User inputs
        - Checkpoints & Breakpoints
            - Branching and diffing
    '''
    UID     = 'Distributed_Execution'
    Version = '1.0'
    Dependencies = [
        ('Monadish','=1.2')
    ]

from .SubModule_Nodes import (_loader_mixins_       as Exec_Loader_Mixins , 
                                   _loader_items_        as Exec_Loader_Items  , 
                                   _new_structure_items_ as Exec_Loader_Structs,
                                   _module_tests_        as Exec_Tests)
for x in Exec_Loader_Items:
    x.Module = main
main._loader_mixins_.extend(Exec_Loader_Mixins)
main._loader_items_ .extend(Exec_Loader_Items)
main._module_tests_ .extend(Exec_Tests)
    #A Submodule loader would be a nice little util to clean this up