# from .utils.statics         import get_data_uuid, get_file_uid, INVALID_UUID
# from ..statics              import _unset
from ..models.struct_module import module, module_test
from ..models.base_node     import socket_group
from .Execution_Types       import _mixin, item
from .Execution_Types       import socket_shapes as st
from typing                 import Self, TypeAlias,AnyStr

import itertools

class op_mixin():
    ''' Creates Op Handler instance'''
class Node_Set(op_mixin):
    ...
class Socket_Slice(op_mixin):
    ...

op_compatable : TypeAlias = Node_Set|Socket_Slice|item.node|item.socket|tuple[item.node]|tuple[item.socket]
op_elem       : TypeAlias = item.node|item.socket

class operation_handler():    
    ''' (possiblly recursive) operation resolution handler with minor filtering of operations and logical left-right 
    Interprets all but Node_Set->Node_Set projection w/out zip
    Passes through (eventually) the base operation on a op_elem->op_elem basis to the shadow dunder handler (ie _or_ from __or__ )
    ''' 
    # Ops_Reset           = ['ilshift', 'ishift']
    Ops_Socket_Directional = ['lshift', 'shift']     # Converts socket to directional tuple
    Ops_Reserved           = ['and', 'iand']         # Operations that not passed onto other objects
    Ops_Logical_Inverse    = {'lshift'  : 'shift' ,
                              'ilshift' : 'ishift'}  # Convert to inverse operation
    Ops_Desc = {
        # '' : {'symbol':'', 'desc':' ', 'returns':type},
        'iand'    : {'symbol':'&='   , 'desc':'Chain Last Operation'               , 'returns':Node_Set,
            'Example' : '(x + y &= z) -> (x+y)&(x+z)'},
        'and'     : {'symbol':'&'    , 'desc':'Joins to Node_Set'                  , 'returns':Node_Set,
            'Example' : '(x & y) -> Node_Set(x,y)'},
        
        'shift'   : {'symbol':'>>'   , 'desc':'Append or apply value to sockets '  , 'returns':op_elem|Node_Set,
            'Example' : 'w/ len(x.outs) == len(x.outs) and same type: (x >> y) -> (x.outs[n]->y.ins[n]) '},
        'ishift'  : {'symbol':'>>='  , 'desc':'Reset Sockets and `shift` into'     , 'returns':op_elem|Node_Set,
            'Example' : '(x>>y /n z>>=y) -> z>>y'},

        'lshift'  : {'symbol':'<<'   , 'desc':'`shift` with inverted syntax'       , 'returns':op_elem|Node_Set,
            'Example' : '(x<<y) -> (y>>z)'},
        'ilshift' : {'symbol':'<<='  , 'desc':'`ishift` with inverted syntax'      , 'returns':op_elem|Node_Set,
            'Example' : '(x<<=y) -> (y>>=z)'},

        'imatmul' : {'symbol':'@='   , 'desc':'When on sockets or delayed nodes, A contextual value set (Reverted at c exit)', 'returns':op_elem|Node_Set|None,
            'Example' : 'with delayed.context(): (z >> a @= b) -> (z >> b)  '},
        
        'invert'  : {'symbol':'~'    , 'desc':'Interpreted on op_elem as a zip flag. Zip uses zip(left,right) to match operations', 'returns':Node_Set,
            'Example' : '(x&y) + ~(a&b) -> (x+a) & (y+b)'},
        
        '_other'   : {'symbol':AnyStr, 'desc':'Passed into the constituant op_elem', 'returns':op_elem|Node_Set|NotImplemented,
            'Example' : '(left + right) -> res:= left._add_(right); res is NotImplimented: res:=right._ladd_(left); res is NotImplimented: raise Error'}, 
    }

    def __init__(self,left:op_compatable,right:op_compatable,operation:str):
        left,right,operation = self.resolve_dir(left,right,operation)
        self.left      = left
        self.right     = right
        self.operation = operation
    
    def resolve_dir(self,left,right,op):
        if op in self.Ops_Logical_Inverse.keys(): 
            return right, left, self.Ops_Logical_Inverse[op]
        else:
            return left , right, op

    def Resolve(self)->op_compatable:
        ''' Evaluate operation to sub-operations as required, Resolve
        Returns are based on sub-operations'''
        ... #TODO Resolve slices
        ... #TODO Det op by l-r contributers, call correct op in matrix (bellow)
        left,right,op = self.left, self.right, self.operation

        left_is_sockets   = isinstance(left,  Socket_Slice)
        right_is_sockets  = isinstance(left,  Socket_Slice)
        if   op in self.Ops_Socket_Directional: 
            if  left_is_sockets : left  = left['out']
            if right_is_sockets : right = right['in']

        zip_flag   = getattr(left,'zip_flag',False) or getattr(left,'zip_flag',True)
        # reset_flag = op in self.Ops_Reset

        if   op == 'iand': return self._sop_iand_(left,right)
        elif op == 'and' : return self._sop_and_( left,right)


        left_is_ns      = isinstance(left, Node_Set) 
        right_is_ns     = isinstance(right, Node_Set) 
        left_is_multi   = left_is_ns  or left_is_sockets  or  isinstance(left,(list,tuple))
        right_is_multi  = right_is_ns or right_is_sockets or  isinstance(right,(list,tuple))

        if       left_is_ns    and     right_is_ns    : return self.nodeset_to_nodeset_nozip(left,right,op,zip_flag)

        elif     left_is_ns    and     right_is_multi : return self.nodeset_to_tuple(left,right,op,zip_flag)
        elif     left_is_multi and     right_is_ns    : return self.tuple_to_nodeset(left,right,op,zip_flag)
        elif right_is_sockets  and     left_is_sockets: return self.socketSlice_to_socketSlice(left,right,op,zip_flag)
        # elif     left_is_multi and     right_is_multi : #Not possible, both would be tuples
        

        elif not left_is_multi and     right_is_multi : return self.one_to_tuple(left,right,op,zip_flag)
        elif     left_is_multi and not right_is_multi : return self.tuple_to_one(left,right,op,zip_flag)
        elif not left_is_multi and not right_is_multi : return self.one_to_one(left,right,op,zip_flag)

        else: raise Exception(f'ERROR COULD NOT RESOLVE MATRIX FOR: {self._er}')


    def _sop_iand_(self,l,r):
        ''' &= operation : (x + y &= z) -> (x+y)&(x+z) '''
    def _sop_and_(self,l,r):
        ''' &  operation : (x&y) -> node_set(x,y)'''

    def one_to_one(self,left,right,op,zip_flag):
        #In zips, do 1 to 1 directional sockets projection.
        ... 

    def one_to_nodeset(self,left,right,op,zip_flag):
        ...
    def nodeset_to_one(self,left,right,op,zip_flag):
        ...

    def tuple_to_nodeset(self,left,right,op,zip_flag):
        ... #Will call r{op}, will need to convert
    def nodeset_to_tuple(self,left,right,op,zip_flag):
        ...

    def one_to_tuple(self,left,right,op,zip_flag):
        ...
    def tuple_to_one(self,left,right,op,zip_flag):
        ...

    ## UNSUPPORTED BY HANDLER:
    def nodeset_to_nodeset(self,left,right,op,zip_flag):
        if not zip_flag: raise Exception(self._er,)

        ...

    def socketSlice_to_socketSlice(self,left,right,op,zip_flag):
        

        if zip_flag: 
            res = []
            if   len(left)  == 1: left  = itertools.repeat(left,len(right))
            elif len(right) == 1: right = itertools.repeat(right,len(left))
            else: assert len(left) == len(right) #TODO: Consider 
            for l,r in zip(left,right):
                res.append(self.__class__(l,r,op).Resolve())
            if not len(res) and len(left) and len(right) : raise Exception('')
            if NotImplemented in res : raise NotImplementedError('')
            if len(res) == 1:
                res = res[0]
            else:
                res = Node_Set(*res)
        else:
            for l in left:
                if func:=(l,'_m_{op}_',None): res.append(func) 
            ...
            


    def _er(self)->str:
        return f'{self.left} -[{self.op}]-> {self.right}'
        ...

class main(module):
    ''' A monad-like interface for creating graphs'''
    UID     = 'Monadish_Interface'
    Version = '1.0'

    class node_mixin(_mixin.node):
        ...
    class socket_mixin(_mixin.socket):
        ...

#### Test Nodes: ####

class new_socket(item.socket):
    Module     = main 
    UID        = 'Test_MonadishNode'
    Version    = '1.0'
    Label      = 'Test_MonadishNode'
    Desc       = ''' Test String Socket '''
    Test_Only  = True
    Value_Type    = str
    Value_Default = 'c'
    
    def __repr__(self):
        try:
            direction = self.dir
        except:
            direction = '?'
        return f'<<< Socket object: {self.UID} @ {self.context.KeyRep('node')}.{direction}_sockets["{getattr(self,'key','?')}"] >>>'
    
class new_exec_node(item.exec_node):
    Module  = main 
    UID     = 'Test_MonadishNode'
    Label   = 'Test_MonadishNode'
    Version = '1.0'
    Desc    = ''' Append socket B to A '''
    Test_Only  = True

    in_sockets   = [socket_group.construct('set_a', Sockets=[new_socket]),
                    socket_group.construct('set_b', Sockets=[new_socket])]
    out_sockets  = [socket_group.construct('set_a', Sockets=[new_socket])]

main._loader_items_ = [new_socket, new_exec_node]


#### Test ####
    
def _basic_test(graph,subgraph):
    with _sb := graph.monad_subgraph(): 
        #Temporary subgraph for housing objects
        n_a = new_exec_node.M('a','b')
        assert n_a.data == 'ab'

        n_b = new_exec_node.M()
        n_a >> n_b 
        'a' >> n_b 
        # n_b['out',1] << 'a' 
        assert n_b['in',1].data  == 'a'
        assert n_b.data == 'aba'
        
        n_c = n_a[0] + n_b[0]
        assert n_c.out_sockets[0].data == n_a.data + n_b.data

        n_c1_main = subgraph.monad_join_in(n_c)
        
        with operation_handler.delay_context():
            n_b['out',1] @= 'c'
            n_c2_main = subgraph.monad_join_in(n_c)
        assert n_b['in',1].data  == 'a'

        assert n_c1_main.out_sockets[0].data == n_c.out_sockets[0].data
        assert n_c1_main is not n_c
        assert n_c2_main is not n_c
        assert n_c2_main.out_sockets[0].data == 'abc'

        #Intakes input sockets 

        # subgraph.join(_sb)

    
    


main._module_tests_.append(module_test('TestA',
                module      = main,
                funcs       = [_basic_test],
                module_iten = {main.UID : main.Version,
                               'Core_Execution':'2.0'}, 
                ))