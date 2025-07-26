from .Execution_Types import _mixin, item

class main():
    class exec_node_mixin(_mixin.exec_node):
        
        def execute(): ...
    
    class placeholder_node_mixin(_mixin.exec_placeholder_node):
        def execute(): ...
        
    class meta_node_mixin(_mixin.meta_node):
        def compile(): ...


