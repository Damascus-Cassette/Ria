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
            self.items = (shape_socket(x) for x in item.Socket_Set_Base) 
            
        elif isinstance(item, tuple):
            self.is_tup = True
            self.items = (shape_socket(x) for x in item)

        elif isinstance(item, socket_group):
            self.is_sg = True
            self.items = (shape_socket(x) for x in item.sockets.values())
        
        self.in_is_filled = False
    
    def __iter__(self):
        for x in self.items: yield item

    def __len__(self):
        return len(self.items)

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
        
        if used_indices_left < len(left): 
            return False
        return resulting_map
                

    def prep_intake(self,left:Self,socket_claims:list=None)->bool|FunctionType:
        ''' FunctionType executes the mapping of two aligned shapes '''
        ''' Assumes will intake if can, so if not all internal sockets are multi, self.filled = True which blocks other items'''
        ''' Resulting Function, if self is potential, will create and use expected existing shape maps'''
        
        if self.in_is_filled: return False

        if (res:=self.generate_mapping(left,socket_claims)) is False: return False 
            
        def generated_intake_func():
            item = self.item
            if self.is_cls:     #is a potential structure item
                with self.src_node.context.cached():
                    item = self.src_node.in_sockets.groups[self.item.Group_ID] = self.item(self.src_node)
            for li,ri in res:
                left.src_node.context.subgraph.links.new()
                left.item[li].connect(item.sockets[ri])

        return generated_intake_func


class socket_collection_mixin(_mixin.socket_collection):
    def _monadish_unused_socket_groups(self,claimed_potential_structures:list[socket_group]=None):
        ''' Yield unused potential from structural definition & add number of times cls apears in claimed arg'''

        if claimed_potential_structures is None: claimed_potential_structures = []

        for potential_group in self.Groups:
            max_inst = potential_group.SocketGroup_Quantity_Max
            inst_current_or_claimed =  len(x for x in self.groups if (isinstance(potential_group)))
            inst_current_or_claimed =+ len(x for x in self.groups if (x in claimed_potential_structures))
            if max_inst < inst_current_or_claimed:
                yield potential_group


class node_mixin(_mixin.node):
    def _monadish_prep_intake(self,left_group)->False|FunctionType:
        ''' Check if left_group can connect to self, left could be tuple[socket],tuple[sg],tuple[node],sg,node, '''
        #TODO Make and Check pool first for patches

    def _monadish_prep_intake_node(self, left_node)->False|FunctionType:
        ''' Intake a series of socket groups to match to this node '''

        left_used_indices    = []
        claimed_potential_s  = []
        claimed_potential_sg = []
        resulting_functions  = []

        # left_groups = []

        left_info  = list((li,l,socket_group_shape(l,src_node=left_node)) for (li, l) in enumerate(left_node.groups)) 
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
        
        if left_used_indices != len(left_info):
            return False
        
        def monadish_connect(self):
            for fullfillment_function in resulting_functions: 
                fullfillment_function()
        return monadish_connect


        

#With this it becomes much simpler to have something like:
#For shape in shapes(left)
    #For shape in shapes(right)
    #for shape in shapes(right_potential) 
        # Should be a function producedlimited generator that references how many times it's abstract type has been used
        # This would prob best be done through a shared dict passed in, or a contextual value.
        # This way if the intake was not executed, the values should evaporate and th next attempt can utilize it

# class shape_utils:
#     def _lr_shape_matcher(left:_shape,right:_shape)->bool|tuple[tuple]:
#         ls_shape_len = len(left)
#         rs_shape_len = len(right)

#         mapped_res         = []
#         used_right_indices = []
#         used_left_indices  = []

#         for li, ls_shape in enumerate(left):
#             if li in used_left_indices: continue
#             for ri, rs_shape in enumerate(right):
#                 if ri in used_right_indices: continue
#                 if rs_shape['links_max'] <= rs_shape['links_used'] : continue #If filled
#                 if ls_shape['out_type'] not in rs_shape['in_types']: continue
#                 # debug_print(li,ri, 'MAPPED IN', rs_shape, ls_shape)
#                 mapped_res.append((li,ri))
#                     #Should switch to names for easier attachment.
#                 used_right_indices.append(ri)
#                 used_left_indices .append(ls_shape)
#                 break

#         debug_print('MAP RESULT:',mapped_res)
        
#         if len(used_left_indices) < len(left):
#             return False
#         else:
#             return mapped_res

# from contextvars import ContextVar

# _debug_print = ContextVar('debug_print',default=False)

# def debug_print(*args,**kwargs):
#     if _debug_print.get(): print(*args,**kwargs)

# def connection_mapping_res(left,right):
    
#     debug_print('CONTNECTION MAPPING RES START!',left,right)
#     debug_print('GROUPS ARE:', list(left.out_sockets.groups.items()))
#     debug_print('GROUPS ARE:', list(right.in_sockets.groups.items()))

#     # lg = left.out_sockets.groups[0]
#     # rg = right.in_sockets.groups[0]    

#     mapped_res         = []
#     used_right_indices = []
#     used_left_indices  = []


#     for li,lg in enumerate(left.out_sockets.groups):
        
#         if li in used_left_indices: continue
#         lg_shape = lg.shape(lg,is_left=True)

#         for ri,rg in enumerate(right.in_sockets.groups):
#             if ri in used_right_indices: continue

#             rg_shape = rg.shape(rg)
#             shape_matches = shape_utils._lr_shape_matcher(lg_shape,rg_shape)

#             debug_print('RES', shape_matches ,lg_shape, 'TO' ,rg_shape)
#             if shape_matches is False: continue
            
#             used_right_indices.append(ri)
#             used_left_indices.append(li)
#             mapped_res.append((li,ri,shape_matches))
#             break


#     if len(used_left_indices) < len(left.out_sockets.groups):
#         return False
#     else:
#         return mapped_res




############ TESTS ############

mapping_tests = [
    # (left,right,expected),
    (node_a1_a1, node_a1_a1, [(0, 0, [(0, 0)])]),
    (node_a1_a1, node_b1_b1, False  ),
    (node_a1_a1, node_c1_c1, [(0, 0, [(0, 0)])]),
    (node_a1_a1, node_c1_c1, [(0, 0, [(0, 0)])]),
    (node_b1_b1, node_a1_a1, False  ),
    (node_b1_b1, node_c1_c1, [(0, 0, [(0, 0)])]),
    (node_b1_b1, node_b1_b1, [(0, 0, [(0, 0)])]),
]

def test_indv(left_base,right_base,expected):
    left   = left_base (default_sockets=True)
    right  = right_base(default_sockets=True)
    result = connection_mapping_res(left,right)
    if not result == expected:
        raise Exception(f'TEST INDV WAS NOT AS EXPECTED: {result} != {expected} w/ {left_base.__name__} -> {right_base.__name__}', )

def test_simple_array(graph,subgraph):
    with subgraph.context.Cached():
        for l,r,res in mapping_tests:
            test_indv(l,r,res)
            

def test_complex_left_right(graph,subgraph):
    _debug_print.set(True)
    debug_print('STARTED TEST COMPLEX ')
    with subgraph.context.Cached():
        left  = node_left_simple_1 (default_sockets=True)
        right = node_right_simple_1(default_sockets=True)
        res   = connection_mapping_res(left,right)
        debug_print(res)
        assert [(0,0,[(0,0),(1,1)]),(1,1,[0,0])] == res

main._module_tests_.append(module_test('TestA',
                module      = main,
                module_iten = {main.UID : main.Version,
                               'Core_Execution':'2.0'}, 
                funcs       = [
                               test_simple_array       ,
                               test_complex_left_right ,
                              ],
                ))