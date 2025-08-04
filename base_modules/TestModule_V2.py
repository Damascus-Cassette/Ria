from ..models.struct_module import module, socket_group
from .Execution_Types       import item,_mixin

class main(module):
    UID          = 'TestModule'
    Label        = 'TestModule'
    Desc         = ''' Adding a few nodes to test base functionality '''
    ChangeLog    = ''' '''
    Version      = '2.0'
    
    Deps = [
        ('required','Core_Execution','=(2.0)','Failure_Message')
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

class new_exec_node(item.exec_node):
    Module  = main 
    UID     = 'TestExecNode'
    Label   = 'TestExecNode'
    Version = '1.0'
    Desc    = ''' Append socket B to A '''
    
    in_sockets   = [socket_group.construct('set_a', Sockets=[new_socket]),
                    socket_group.construct('set_b', Sockets=[new_socket])]
    out_sockets  = [socket_group.construct('set_a', Sockets=[new_socket])]

    def execute(self):
        self.out_sockets[0].value = self.in_sockets[0].value + self.in_sockets[1].value
        self.test_module_executed = True

def basic_exec_test(graph):
    nodea = new_exec_node(default_sockets=True)
    nodeb = new_exec_node(default_sockets=True)

    nodea.in_sockets[0].value = 'a'
    nodea.in_sockets[1].value = 'b'
    nodeb.in_sockets[1].value = 'c'
    # nodea.in_sockets.set(['a','b'])
    
    graph.nodes.extend([nodea,nodeb])
    graph.links.new(out_socket = nodea.out_sockets[0], 
                    in_socket  = nodeb.in_sockets[0])

    v = nodeb.out_sockets[0].value
    assert nodea.test_module_executed == True
    assert nodeb.test_module_executed == True
    assert v == 'abc'

    return nodea,nodeb

def adv_exec_test(graph):
    nodea,nodeb = basic_exec_test(graph)
    nodea.test_module_executed = False
    nodeb.test_module_executed = False

    v = nodeb.out_sockets[0].value
    assert nodea.test_module_executed == False
    assert nodeb.test_module_executed == True
    assert v == 'abc'
    v = nodeb.out_sockets[0].value

main._test_module.extend([
    basic_exec_test,
    adv_exec_test,
])

main._loader_items_.extend([
    new_socket,
    new_exec_node,
    ])