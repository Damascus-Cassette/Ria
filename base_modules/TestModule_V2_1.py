from ..models.struct_module import module
from ..models import base_node
from .Execution_Types       import item,_mixin
from ..model.factories      import node_factory

class main(module):
    UID          = 'TestModule'
    Label        = 'TestModule'
    Desc         = ''' Add factory methods '''
    ChangeLog    = ''' '''
    Version      = '2.1'
    
    Deps = [
        ('required','Core_Execution','=(3.0)','Failure_Message')
        ]
    
    _test_module_ = []
        #testing funcs go in here

class new_socket(item.socket):
    Module  = main 
    UID     = 'StringSocket'
    Version = '1.0'
    Label   = 'StringSocket'
    Desc    = ''' Test String Socket '''
    
    Value_Types    = [str]
    Value_Allow    = [str]

    Value_Default  = ''
    Disc_Cachable  = True

@item.node.factory(UID='TestExecNode1',Version='1.0')
def new_exec_node1(a:str,b:str)->str:
    return a+b

@item.node.factory(UID='TestExecNode2',Version='1.0', out_shape={'a':str,'b':'default','c':new_socket,'d':int})
def new_exec_node2(a:str,b:str)->dict[str|int]:
    ''' Shape definition can be used'''
    return {'a':'','b':'','c':'','d':0}

@item.node.factory(UID='TestExecNode3',Version='1.0', mem_cachable=True, disc_cachable=False)
def new_exec_node3(a:base_node.graph,b:str):
    ''' Typed inputs to env singletons produce side sockets '''
    return a.name + b

@item.node.factory(UID='TestExecNode4',Version='1.0', deterministic = False)
def new_exec_node4(a:base_node.context,b:str):
    ''' Typed inputs to conte '''
    return a.graph.name

module.add_items(
    new_exec_node1,
    new_exec_node2,
    new_exec_node3,
    new_exec_node4,
)

def basic_exec_test(graph):
    ...

main._test_module.extend([
    basic_exec_test,
])

main._loader_items_.extend([
    new_socket,
    ])