''' Atomic focused rewrite to monadish, with testing of each indivdual action '''

from ..models.struct_module import module, module_test
from ..models.base_node     import socket_group
from .Execution_Types       import _mixin, item
# from .Execution_Types       import socket_shapes as st

from typing                 import Any, Self, TypeAlias,AnyStr,Type
from types                  import FunctionType
from inspect                import isclass


class utils:
    def iter_unseen(*iterables):
        seen = []
        for iterable in iterables:
            for x in iterable:
                if not (x in seen):
                    yield x


class main(module):
    ''' A monad-like interface for creating graphs'''
    UID     = 'Monadish_Interface'
    Version = '1.0'



############ CLASSES ############

_shape : TypeAlias = list[dict]

class socket_group_mixin(_mixin.socket_group):
    # def Shape as class method??
    #TODO: Make work in the class as well
    
    @staticmethod
    def shape(self_or_cls:Self,is_left=False)->_shape:
        ''' If is_left, return actual tuple, else as any '''
        ''' Next check in this module make inst and have return func to connect '''
        if isclass(self_or_cls): return self_or_cls._inst_shape(is_left = is_left)
        else:                    return self_or_cls._inst_shape(is_left = is_left)
    
    @classmethod
    def _cls_shape(cls,is_left=False)-> _shape:
        # assert not is_left
        # Cannot match left sockets shapes?
        res = []
        for socket_cls in cls.Socket_Set_Base:
            res.append({'in_types'     : socket_cls.Value_In_Types          ,
                        'out_type'     : socket_cls.Value_Out_Type          ,
                        'links_max'    : socket_cls.Link_Quantity_Max       ,
                        'links_used'   : 0                                  ,
                        'is_potential' : True                               ,
                        'src'          : cls                                ,
                        })
        return res

    def _inst_shape(self,is_left=False) -> _shape:
        res = []
        for socket in self.sockets.values():
            res.append({'in_types'     : socket.Value_In_Types          ,
                        'out_type'     : socket.Value_Out_Type          ,
                        'links_max'    : socket.Link_Quantity_Max       ,
                        'links_used'   : len(socket.links)              ,
                        'is_potential' : False                          ,
                        'src'          : self                           ,
                        })
        return res


                

main._loader_mixins_ = [socket_group_mixin]



############ TEST NODES ############

class a_socket(item.socket):
    Module     = main 
    UID        = 'Test_MonadSocket_A'
    Version    = '1.0'
    Label      = 'Test_MonadSocket_A'

    Value_In_Types    = str
    Value_Out_Type    = str
    Value_Default     = 'c'

class b_socket(item.socket):
    Module     = main 
    UID        = 'Test_MonadSocket_B'
    Version    = '1.0'
    Label      = 'Test_MonadSocket_B'

    Value_In_Types    = int
    Value_Out_Type    = int
    Value_Default     = 'c'

class c_socket(item.socket):
    Module     = main 
    UID        = 'Test_MonadSocket_C'
    Version    = '1.0'
    Label      = 'Test_MonadSocket_C'

    Value_In_Types    = (int,str)
    Value_Out_Type    = str
    Value_Default     = 'c'

class node_a1_a1(item.exec_node):
    Module  = main 
    UID     = 'node_a1_a1'
    Label   = 'node_a1_a1'
    Version = '1.0'

    in_sockets    = [socket_group.construct('set_a', Sockets=[a_socket])]
    out_sockets   = [socket_group.construct('set_a', Sockets=[a_socket])]
    # side_sockets  = [socket_group.construct('set_a', Sockets=[a_socket])]

class node_b1_b1(node_a1_a1):
    in_sockets    = [socket_group.construct('set_a', Sockets=[b_socket])]
    out_sockets   = [socket_group.construct('set_a', Sockets=[b_socket])]

class node_c1_c1(node_a1_a1):
    in_sockets    = [socket_group.construct('set_a', Sockets=[c_socket])]
    out_sockets   = [socket_group.construct('set_a', Sockets=[c_socket])]


class node_left_simple_1(node_a1_a1):
    in_sockets   = []
    side_sockets = []
    out_sockets  = [socket_group.construct('set_a', Sockets=[a_socket,
                                                             c_socket]),
                    socket_group.construct('set_a', Sockets=[b_socket])]

class node_right_simple_1(node_a1_a1):
    side_sockets = []
    out_sockets  = []
    in_sockets   = [socket_group.construct('set_a', Sockets=[a_socket,
                                                             c_socket]),
                    socket_group.construct('set_a', Sockets=[b_socket])]

main._loader_items_ = [a_socket            ,
                       b_socket            ,
                       c_socket            ,
                       node_a1_a1          , 
                       node_b1_b1          ,
                       node_c1_c1          ,
                       node_left_simple_1  ,
                       node_right_simple_1 ,
                       ]



############ FUNCTIONS ############

class shape_utils:
    def _lr_shape_matcher(left:_shape,right:_shape)->bool|tuple[tuple]:
        ls_shape_len = len(left)
        rs_shape_len = len(right)

        mapped_res         = []
        used_right_indices = []
        used_left_indices  = []

        for li, ls_shape in enumerate(left):
            for ri, rs_shape in enumerate(right):
                if rs_shape['links_max'] <= rs_shape['links_used']: continue #If filled
                if ri in used_right_indices: continue
                if ls_shape['out_type'] in rs_shape['in_types']:
                    mapped_res.append((li,ri))
                    used_right_indices.append(ri)
                    used_left_indices .append(ls_shape)
                    break
        
        if len(used_left_indices) < len(left):
            return False
        else:
            return mapped_res
            
def connection_mapping_res(left,right):
    #TODO: Make so iterate over each shape, find matches.
    
    print(left.in_sockets.groups)

    lg = left.out_sockets.groups[0]
    rg = right.in_sockets.groups[0]    

    lg_shape = lg.shape(lg,is_left=True)
    rg_shape = rg.shape(rg,)

    return shape_utils._lr_shape_matcher(lg_shape,rg_shape)



############ TESTS ############

mapping_tests = [
    # (left,right,expected),
    (node_a1_a1, node_a1_a1, [(0,0)]),
    (node_a1_a1, node_b1_b1, False  ),
    (node_a1_a1, node_c1_c1, [(0,0)]),
    (node_a1_a1, node_c1_c1, [(0,0)]),
    (node_b1_b1, node_a1_a1, False  ),
    (node_b1_b1, node_c1_c1, [(0,0)]),
    (node_b1_b1, node_b1_b1, [(0,0)]),
]

def test_indv(left_base,right_base,expected):
    left   = left_base (default_sockets=True)
    right  = right_base(default_sockets=True)
    result = connection_mapping_res(left,right)
    assert result == expected

def test_simple_array(graph,subgraph):
    with subgraph.context.Cached():
        for l,r,res in mapping_tests:
            test_indv(l,r,res)
            

def test_complex_left_right(graph,subgraph):
    with subgraph.context.Cached():
        left  = node_left_simple_1 (default_sockets=True)
        right = node_right_simple_1(default_sockets=True)
        res   = connection_mapping_res(left,right)
        assert [(0,0),(1,1)] == res

main._module_tests_.append(module_test('TestA',
                module      = main,
                module_iten = {main.UID : main.Version,
                               'Core_Execution':'2.0'}, 
                funcs       = [
                               test_simple_array       ,
                               test_complex_left_right ,
                              ],
                ))