from ..models.struct_module    import module, module_test
from ..models.struct_hook_base import hook
from ..models.base_node        import socket_group
from .Execution_Types          import item,_mixin
from .utils.print_debug        import debug_print_wrapper as debug_wraper, debug_print as dprint

from contextvars import ContextVar

test_var = ContextVar('test_var',default=False)
class main(module):
    UID          = 'TestModule'
    Label        = 'TestModule'
    Desc         = ''' Adding a few nodes to test base functionality '''
    ChangeLog    = ''' '''
    Version      = '2.0'
    
    
    class node_collection_mixin(_mixin.node_collection):

        @hook(event='__setitem__', mode='post')
        def _new(self,item):
            test_var.set(True)
            # raise Exception('DAS SCREEMING CHICKEN')
        

    Deps = [
        ('required','Core_Execution','=(2.0)','Failure_Message')
        ]

class new_socket(item.socket):
    # @classmethod
    # def Construct(cls,recur):raise Exception(getattr(cls,'_constr_bases_key_',None))
    Module     = main 
    UID        = 'StringSocket'
    Version    = '1.0'
    Label      = 'StringSocket'
    Desc       = ''' Test String Socket '''
    Value_Type    = str
    Value_Default = 'c'

        
    # def __repr__(self):
    #     # Consider adding similar procedural on datastruct for generic access
    #     # Would need fallbacks for a not fully initlized object like I found below
    #     # return f'<<< Socket object: {self.UID} @ (graph).["{self.context.node.key}"].{self.dir}_sockets["{self.key}"] >>>'
    #     try:
    #         direction = self.dir
    #     except:
    #         direction = '?'
    #     return f'<<< Socket object: {self.UID} @ {self.context.KeyRep('node')}.{direction}_sockets["{getattr(self,'key','?')}"] >>>'
    
class new_exec_node(item.exec_node):
    Module  = main 
    UID     = 'TestExecNode'
    Label   = 'TestExecNode'
    Version = '1.0'
    Desc    = ''' Append socket B to A '''

    test_module_executed = False

    
    in_sockets   = [socket_group.construct('set_a', Sockets=[new_socket]),
                    socket_group.construct('set_b', Sockets=[new_socket])]
    out_sockets  = [socket_group.construct('set_a', Sockets=[new_socket])]

    @debug_wraper()
    def execute(self):
        self.test_module_executed = True        
        # print('self.in_sockets[0]',self.in_sockets[0].Value_Shape.get(self.in_sockets[0]))
        #erros raised during implicit execution don't work????????

        i1 = self.in_sockets[0].value
        i2 = self.in_sockets[1].value
        # print (i1,i2)
        val = i1 + i2
        self.out_sockets[0].value = val
        return val

main._loader_items_.extend([
    new_socket,
    new_exec_node,
    ])



###### TESTS ######

def basic_exec_test(graph,subgraph):
    # with subgraph.context.Cached():
    with subgraph.As_Env(auto_add_nodes = True, auto_add_links = True):
        nodea = new_exec_node(default_sockets=True)
        nodeb = new_exec_node(default_sockets=True)

        # print({k:v for k,v in nodea.in_sockets.items()})
        nodea.in_sockets[0].value = 'a'
        nodea.in_sockets[1].value = 'b'

        nodeb.in_sockets[1].value = 'c'
        # nodea.in_sockets.set(['a','b'])
        
        subgraph.nodes['nodea'] = nodea
        subgraph.nodes['nodeb'] = nodeb
        link_a = subgraph.links.new(key='Link',
                           out_socket = nodea.out_sockets[0], 
                           in_socket  = nodeb.in_sockets[0])
        b = True

    assert nodea.context.subgraph == subgraph
    
    assert b
    assert link_a in nodea.out_sockets[0].links.values()
    assert link_a in nodeb.in_sockets[0].links.values()

    v = nodeb.out_sockets[0].value
    assert nodea.test_module_executed == True
    assert nodeb.test_module_executed == True
    assert v == 'abc'

    return nodea,nodeb


def adv_exec_test(graph,subgraph):
    from ..statics import _unset

    nodea,nodeb = basic_exec_test(graph,subgraph)
    nodea.test_module_executed = False
    nodeb.test_module_executed = False

    v = nodeb.out_sockets[0].value
    assert nodea.test_module_executed == False
    assert nodeb.test_module_executed == False

    nodeb.out_sockets[0].value = _unset
    v = nodeb.out_sockets[0].value 
    assert nodeb.test_module_executed == True
    assert nodea.test_module_executed == False

    assert v == 'abc'

def hook_test(graph,subgraph):
    # print(subgraph.nodes._hooks)
    # print(subgraph.nodes.new)
    from pprint import pprint

    print('-'*20)
    print('-'*20)
    print('-'*20)
    # hg = subgraph.nodes.__hooks_initialize__()
    print('-'*20)
    pprint(subgraph.nodes._hooks)
    pprint(hg)

    pprint(subgraph.nodes._hooks.parent_cls)
    print('Anon Hooks:')
    pprint(subgraph.nodes._hooks.anon_hooks)

    print('Named Hooks:')
    pprint(subgraph.nodes._hooks.named_hooks)

    print('Hooked:')
    pprint(subgraph.nodes._hooks.hooked)

    raise Exception('')

def assert_hook_working(graph,subgraph):
    test_var.set(False) 
    subgraph.nodes.new(new_exec_node.UID, key = 'test')
    assert test_var.get() 

main._module_tests_.append(module_test('TestA',
                module      = main,
                funcs       = [
                    assert_hook_working,
                    basic_exec_test ,
                    adv_exec_test   ,
                    # hook_test       ,
                    ],
                module_iten = {main.UID : main.Version,
                               'Core_Execution':'2.0'}, 
                ))
