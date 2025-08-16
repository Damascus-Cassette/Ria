''' Atomic focused rewrite to monadish, with testing of each indivdual action '''

from ..models.struct_module import module, module_test
from ..models.base_node     import socket_group
from .Execution_Types       import _mixin, item
# from .Execution_Types       import socket_shapes as st

from typing                 import Any, Self, TypeAlias,AnyStr,Type
from types                  import FunctionType
from inspect                import isclass

from .utils.print_debug import (debug_print_wrapper as dp_wrap, debug_level,debug_targets, _debug_print as dprint)

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


# class socket_group_mixin(_mixin.socket_group): 
    # Currently socket_group_shape is better as an external inspection instead of internal, since
    # Classes cannot determine what they are tied to (only instances can via context)
    # ...

# main._loader_mixins_ = [socket_group_mixin]




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
    out_sockets  = [socket_group.construct('side_a1', Sockets=[a_socket,
                                                               c_socket]),
                    socket_group.construct('side_a1', Sockets=[b_socket])]

class node_right_simple_1(node_a1_a1):
    side_sockets = []
    out_sockets  = []
    in_sockets   = [socket_group.construct('side_b1', Sockets=[a_socket,
                                                               c_socket]),
                    socket_group.construct('side_b2', Sockets=[b_socket])]

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

# class _pass ():...
# class _value():
#     def __init__(self,value):
#         ...

class shape_socket():
    ''' Temporary 'Shape' of an actual or potential socket. '''
    is_cls    : bool = False 
    src_group : Any  = None
    src_node  : Any  = None

    def __init__(self,
                 item:_mixin.socket,
                 src_group = None,
                 src_node  = None):

        if isclass(item): 
            self.is_cls = True
            self.src_group = src_group
            self.src_node  = src_node
            assert src_group
            assert src_node
        self.item = item
        
    @property
    def in_types(self):
        return self.item.Value_In_Types
    @property
    def out_type(self):
        return self.item.Value_Out_Type
    @property
    def links_max(self):
        return self.item.Link_Quantity_Max
        
    @property
    def links_used(self):
        if self.is_cls: return 0
        return len(self.item.links)
    @property
    def in_is_filled(self):
        #TODO: May have to add a counter of potentials in a context/temporary variable pre-application
        if (lm:=self.links_max) == 'n': return False
        return self.links_max <= self.links_used

    @property
    def is_potential(self):
        return self.is_cls
    
    def can_intake(self,left:Self):
        return (left.out_type in self.in_types) and (not self.in_is_filled)
    
    def connect(self,right_socket):
        return self.item.context.subgraph.links.new(left  = self.item, 
                                                    right = right_socket)
        # return self.src_node.context.subgraph.links.new(left  = self.item, 
        #                                                 right = right_socket)
    
class socket_group_shape():
    ''' Intermediatary socket group shape, used as a proxy for allowing inst,cls, and tuples[socket|_value|_skip].'''
    src_item : Any = None
    src_node : Any = None
    
    items   : list[shape_socket]
    
    is_tup = False
    is_sg  = False
    is_cls = False  #effectivly is potential

    @property
    def in_is_filled(self):
        return any(x.in_is_filled for x in self.items)

    def __init__(self ,  
                 item      : _mixin.socket_group|_mixin.socket|tuple[_mixin.socket],
                 src_node  : _mixin.node = None,
                 ):
        
        #item = groupinst_or_cls_or_tuple
        self.src_item = item
        self.src_node = src_node
            
        if isclass(item):
            assert src_node
            self.is_sg = True
            self.items = list(shape_socket(x) for x in item.Socket_Set_Base) 
            
        elif isinstance(item, tuple):
            self.is_tup = True
            self.items = list(shape_socket(x) for x in item)

        elif isinstance(item, socket_group):
            self.is_sg = True
            self.items = list(shape_socket(x) for x in item.sockets.values())
    
    def __iter__(self):
        for x in self.items: yield x

    def __len__(self):
        return len(self.items)

    @dp_wrap(print_result=True)
    def generate_mapping(self, left:Self, socket_claims:list=None)->bool|list[tuple]:
        ''' Attempts to generate mapping from left.items to self.items for connection, if it's not able to, return false '''
        ''' Actual object references are not exactltly possible, as the structure may be potential. The resulting func however will get the l_sg and r_sg passed in'''
        if socket_claims is None: socket_claims = []
        used_indices_left  = []
        used_indices_right = []
        resulting_map      = []

        for li,l in enumerate(left):
            for ri,r in enumerate(self):

                if ri in used_indices_right: 
                    continue
                if r.can_intake(l):
                    used_indices_left.append(li)
                    used_indices_right.append(ri)
                    resulting_map.append((li,ri))
                    break
        
        if len(used_indices_left) < len(left): 
            return False
        return resulting_map
                
    @dp_wrap(print_result=True)
    def prep_intake(self, left:Self, socket_claims:list=None)->bool|FunctionType:
        ''' FunctionType executes the mapping of two aligned shapes '''
        ''' Assumes will intake if can, so if not all internal sockets are multi, self.filled = True which blocks other items'''
        ''' Resulting Function, if self is potential, will create and use expected existing shape maps'''
        
        if self.in_is_filled: return False

        if (res:=self.generate_mapping(left,socket_claims)) is False: return False 
            
        def generated_intake_func(debug_return_fullfillment=False):

            if debug_return_fullfillment: 
                return (left.src_item,self.src_item,res)
            item = self.src_item
            if self.is_cls:     #is a potential structure item
                with self.src_node.context.cached():
                    item = self.src_item(self.src_node)
                    self.src_node.in_sockets.groups[self.src_item.Group_ID] = item
            for li,ri in res:
                left.src_node.context.subgraph.links.new()
                left.src_item[li].connect(item.sockets[ri])

        return generated_intake_func

class socket_collection_mixin(_mixin.socket_collection):
    def _monadish_unused_socket_groups(self,claimed_potential_structures:list[socket_group]=None):
        ''' Yield unused potential from structural definition & add number of times cls apears in claimed arg'''

        if claimed_potential_structures is None: claimed_potential_structures = []

        for potential_group in self.Groups:
            max_inst = potential_group.SocketGroup_Quantity_Max
            inst_current_or_claimed =  len([x for x in self.groups if (isinstance(x, potential_group))])
            inst_current_or_claimed =+ len([x for x in self.groups if (x in claimed_potential_structures)])
            if max_inst < inst_current_or_claimed:
                yield potential_group

class node_mixin(_mixin.node):
    def _monadish_prep_intake(self,left_group)->bool|FunctionType:
        ''' Check if left_group can connect to self, left could be tuple[socket],tuple[sg],tuple[node],sg,node, '''
        #TODO Make and Check pool first for patches

    @dp_wrap(print_result=True)
    def _monadish_prep_intake_node(self, left_node)->bool|FunctionType:
        ''' Intake a series of socket groups to match to this node '''

        left_used_indices    = []
        claimed_potential_s  = []
        claimed_potential_sg = []
        resulting_functions  = []

        # left_groups = []

        left_info  = list((li,l,socket_group_shape(l,src_node=left_node)) for (li, l) in enumerate(left_node.out_sockets.groups)) 
        right_info = list((ri,r,socket_group_shape(r,src_node=self     )) for (ri, r) in enumerate(self.in_sockets.groups))

        for li, left_group, left_shape in left_info:
            if li in left_used_indices: continue
                    
            for ri, right_group, right_shape in right_info:
                if right_shape.in_is_filled: continue
                res = right_shape.prep_intake(left_shape,claimed_potential_s)
                if res is False: continue
                left_used_indices.append(li)
                resulting_functions.append(res)
                break

            if li in left_used_indices: continue

            for potential_sg in self.in_sockets._monadish_unused_socket_groups(claimed_potential_sg):
                p_r_shape = socket_group_shape(potential_sg)
                res = p_r_shape.prep_intake(left_shape)
                if res is False: continue
                left_used_indices.append(li)
                resulting_functions.append(res)
                claimed_potential_sg.append(potential_sg)
                break
        
        if len(left_used_indices) != len(left_info):
            return False
        
        def monadish_connect(debug_return_fullfillment:bool=False):
            res  = []
            for fullfillment_function in resulting_functions: 
                res.append(fullfillment_function(debug_return_fullfillment=debug_return_fullfillment))
            return res
        
        return monadish_connect


main._loader_mixins_ = [
    socket_collection_mixin,
    node_mixin
    ]

############ TESTS ############

# mapping_tests = [
#     # (left,right,expected),
#     (node_a1_a1, node_a1_a1, [(0, 0, [(0, 0)])]),
#     (node_a1_a1, node_b1_b1, False  ),
#     (node_a1_a1, node_c1_c1, [(0, 0, [(0, 0)])]),
#     (node_a1_a1, node_c1_c1, [(0, 0, [(0, 0)])]),
#     (node_b1_b1, node_a1_a1, False  ),
#     (node_b1_b1, node_c1_c1, [(0, 0, [(0, 0)])]),
#     (node_b1_b1, node_b1_b1, [(0, 0, [(0, 0)])]),
# ]

def new_test(graph,subgraph):
    with subgraph.context.Cached():
        # with debug_level(4):
        with debug_targets({'Monadish_Interface_1_1': 4 }):
            left  = node_left_simple_1 (default_sockets=True)
            right = node_right_simple_1(default_sockets=True)
            print(*left.out_sockets.groups)
            print(*right.in_sockets.groups)

            res = right._monadish_prep_intake_node(left)
            # assert isinstance(res,FunctionType)
            res = res(debug_return_fullfillment=True)
            dprint(res)

            raise Exception('')

main._module_tests_.append(module_test('TestA',
                module      = main,
                module_iten = {main.UID : main.Version,
                               'Core_Execution':'2.0'}, 
                funcs       = [
                                new_test,
                            #    test_simple_array       ,
                            #    test_complex_left_right ,
                              ],
                ))