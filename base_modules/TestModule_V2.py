from ..models.struct_module import module, module_test
from ..models.base_node     import socket_group
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

class new_socket(item.socket):
    Module     = main 
    UID        = 'StringSocket'
    Version    = '1.0'
    Label      = 'StringSocket'
    Desc       = ''' Test String Socket '''
    Value_Type    = str
    Value_Default = 'c'

        
    def __repr__(self):
        # Consider adding similar procedural on datastruct for generic access
        # Would need fallbacks for a not fully initlized object like I found below
        # return f'<<< Socket object: {self.UID} @ (graph).["{self.context.node.key}"].{self.dir}_sockets["{self.key}"] >>>'
        try:
            direction = self.dir
        except:
            direction = '?'
        return f'<<< Socket object: {self.UID} @ {self.context.KeyRep('node')}.{direction}_sockets["{getattr(self,'key','?')}"] >>>'
    
class new_exec_node(item.exec_node):
    Module  = main 
    UID     = 'TestExecNode'
    Label   = 'TestExecNode'
    Version = '1.0'
    Desc    = ''' Append socket B to A '''

    def __repr__(self):
        return f'<<< Node object: {self.UID} @ (graph).["{self.key}"] >>>'
    
    in_sockets   = [socket_group.construct('set_a', Sockets=[new_socket]),
                    socket_group.construct('set_b', Sockets=[new_socket])]
    out_sockets  = [socket_group.construct('set_a', Sockets=[new_socket])]

    def execute(self):
        print(f'CALLED EXECUTE FUCKER : {self}')
        self.test_module_executed = True        
        # print('self.in_sockets[0]',self.in_sockets[0].Value_Shape.get(self.in_sockets[0]))
        #erros raised during implicit execution don't work????????

        i1 = self.in_sockets[0].value_get()
        i2 = self.in_sockets[1].value_get()
        print (i1,i2)
        val = i1 + i2
        self.out_sockets[0].value_set(val)
        print(f'EXECUTED {self.key} Result = {val}') 
        return val

main._loader_items_.extend([
    new_socket,
    new_exec_node,
    ])



###### TESTS ######

def basic_exec_test(graph,subgraph):
    with subgraph.context.Cached():
        nodea = new_exec_node(default_sockets=True)
        nodeb = new_exec_node(default_sockets=True)

        nodea.in_sockets[0].value_set = 'a'
        nodea.in_sockets[1].value_set = 'b'
        nodeb.in_sockets[1].value_set = 'c'
        # nodea.in_sockets.set(['a','b'])
        
        subgraph.nodes['nodea'] = nodea
        subgraph.nodes['nodeb'] = nodeb
        link_a = subgraph.links.new(key='',
                           out_socket = nodea.out_sockets[0], 
                           in_socket  = nodeb.in_sockets[0])

    print(link_a)
    print(nodea.out_sockets[0].out_links._data)

    v = nodeb.out_sockets[0].value_get()
    assert nodea.test_module_executed == True
    assert nodeb.test_module_executed == True
    assert v == 'abc'

    return nodea,nodeb

def adv_exec_test(r_graph,graph):
    nodea,nodeb = basic_exec_test(graph)
    nodea.test_module_executed = False
    nodeb.test_module_executed = False

    v = nodeb.out_sockets[0].value
    assert nodea.test_module_executed == False
    assert nodeb.test_module_executed == True
    assert v == 'abc'
    v = nodeb.out_sockets[0].value

main._module_tests_.append(module_test('TestA',
                module      = main,
                funcs       = [basic_exec_test,adv_exec_test],
                module_iten = {main.UID : main.Version,
                               'Core_Execution':'2.0'}, 
                ))
