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
        ('Monadish_Interface','=1.2')
    ]



from .Submodule_ExecFlow  import _exec_flow_mixins_, _exec_flow_items_, _exec_flow_tests_
for x in _exec_flow_items_: x.Module = main
for x in _exec_flow_tests_: x.module = main

main._loader_mixins_.extend(_exec_flow_mixins_)
main._loader_items_ .extend(_exec_flow_items_ )
main._module_tests_ .extend(_exec_flow_tests_ )

from .Submodule_Cache     import _cache_mixins_    , _cache_items_    , _cache_tests_
for x in _cache_items_: x.Module = main
for x in _cache_tests_: x.module = main

main._loader_mixins_.extend(_cache_mixins_)
main._loader_items_ .extend(_cache_items_ )
main._module_tests_ .extend(_cache_tests_ )

from .Submodule_StateKey  import _statekey_mixins_    , _statekey_items_    , _statekey_tests_
for x in _statekey_items_: x.Module = main
for x in _statekey_tests_: x.module = main

main._loader_mixins_.extend(_cache_mixins_)
main._loader_items_ .extend(_cache_items_ )
main._module_tests_ .extend(_cache_tests_ )

from .Test_Items          import _test_items_
main._loader_items_ .extend(_test_items_)


    #A Submodule loader would be a nice little util to clean this up