# from .utils.statics         import get_data_uuid, get_file_uid, INVALID_UUID
# from ..statics              import _unset
from ..models.struct_module import module, module_test
from ..models.base_node     import socket_group
from .Execution_Types       import _mixin, item
from .Execution_Types       import socket_shapes as st
from typing                 import Self, TypeAlias,AnyStr,Type,
from types import FunctionType
import itertools

def iter_unseen(*iterables):
    seen = []
    for iterable in iterables:
        for x in iterable:
            if not (x in seen):
                yield x

#### TYPES

op_elem     : TypeAlias = item.socket|item.node|'object_set'|'socket_slice'
sslice_keys : TypeAlias = str|int|Type|tuple[str,str|int|Type]

Projection_Rules = '''
- LEFT op RIGHT cannot be of the same object_set type or base, as best projection is uncertain/obscured in the pattern of operation
    - To declare operating modes inline:
        - ~ inver operation as a Zip projection flag (On either party)
        - * splat operation as a convertion to tuple, which is handled as a chain operatior.
        - right.project(mode:str,left) for manual declaration and more options.

- Default projection between not (object_set op object_set) is chain 
    - it's works for projection of 1 to many, and simplification of 
    - chain utilizes left = itertools.repeat(left,len(right))

- Zip Projection is non-default and throws error if safe(default) and acts as
    - for l,r in zip(l,r): res.append(l.op(right))

'''

class operation_handler():
    Ops_Inv_Direction = {'ilshift':'ishift', #Directional inversion from_op : to_op
                         'lshift' :'rshift' }
    
    Ops_Directional   = ['rshift' ,'irshift']
        #Operations that require slice to relevent object_set
        #Simplfieid if arithmatic
    
    Ops_Special       = ['iand'  ,'irshift','and'] #Ops that run a pre-process to change the operation on execution 
    Ops_Mutagenic     = ['rshift' , ]

    
    def sop_and(self):
        right = object_set(self.left,self.right)
        return ..., right, 'pass'     

    def sop_iand(self):
        #TODO: Determine Operation based on contents, split graph for context, set value. Append goal to inverse operations.
        return self.left,self.right,'iand'     

    def sop_irshift(self):
        #TODO: if in delyed context, Determine Operation based on contents, split graph for context, set value. Append goal to inverse operations.
        return self.left,self.right,'rshift' 


    def op_type(self,op):
        if op in self.Ops_Special   : return 'Special'
        if op in self.Ops_Mutagenic : return 'Mutagenic'
        else                        : return 'Arithmatic'

    def __init__(self,left,right,op,is_root=False):
        self.zip_flag = getattr(left,'zip_flag',False) or getattr(right,'zip_flag',False)
            #As may mutate left,right, get zip_flag here
        
        if op in self.Ops_Inv_Direction.keys():
            op = self.Ops_Inv_Direction[op]
            left,right = right,left

        if op in self.Ops_Directional:
            op_t = self.op_type(op)
            if   op_t == 'Arithmatic':
                if isinstance(left ,socket_slice): left  = left.o
                if isinstance(right,socket_slice): right = right.o
            elif op_t == 'Mutagenic':

                if isinstance(left ,socket_slice): left  = left.o
                if isinstance(right,socket_slice): right = right.i
            elif op_t == 'Special' :
                pass #Special operations should socket slices
            else:
                raise Exception(f'Could Not Determine Op Type: {op}') 
        
        self.is_root = is_root
        self.left    = left
        self.right   = right
        self.op      = op

    def _ensure_objset_from_tuple(self,item):
        if isinstance(item,tuple):
            return object_set(*item)
            #TEST IF WAS OBJECT_SET
        return item
        
    def Resolve(self):
        ''' Currently written as only regular arithmatic ops '''
        if self.op in self.Ops_Special:
            left,right,op = getattr(self,f'sop_{op}')()
        else:
            left  = self._ensure_objset_from_tuple(self.left ) 
            right = self._ensure_objset_from_tuple(self.right)
            op    = self.op

        if op == 'PASS':
            if isinstance(right,ellipsis):
                return left
            return right 
        if isinstance(right,ellipsis):
            return left

        zip_flag = self.zip_flag
        
        _lwt  = isinstance(self.left ,tuple)
        _rwt  = isinstance(self.right,tuple)
        was_tupl = _lwt or _rwt

        _l_is_multi = isinstance(left, object_set)
        _r_is_multi = isinstance(right,object_set)

        if isinstance(left,object_set) and isinstance(right,object_set) and not (zip_flag or was_tupl):
            raise NotImplementedError(f'SEE PROJECTION RULES. Short  ~ -> zip_flag, * -> splat op to tuple for chain project ') 
        
        # if (not _l_is_multi) and _r_is_multi and zip_flag:
        #     left = itertools.repeat((left,),len(right))
        
        if   _r_is_multi and zip_flag:
            res =  self.try_resolve_op_1_to_multi(left,right, op,'zip',)
            if not (res is NotImplemented): return res
            res =  right.project('zip', left)
        elif _r_is_multi and was_tupl:
            res =  self.try_resolve_op_1_to_multi(left,right, op,'chain',)
            if not (res is NotImplemented): return res
            res = right.project('chain', left)
        
        elif _l_is_multi and zip_flag: 
            res =  self.try_resolve_op_multi_to_1(left,right, op,'zip',)
            if not (res is NotImplemented): return res
            res = left.lproject('zip', right)
        elif _l_is_multi and was_tupl: 
            res =  self.try_resolve_op_multi_to_1(left,right, op, 'chain')
            if not (res is NotImplemented): return res
            res = left.lproject('chain', right)
        else:
            res = self.try_resolve_op_1_to_1(left,right,op,)
        
        if self.is_root and (res is NotImplemented):
            raise  NotImplementedError(f'COULD NOT RESOLVE OPERATION: {self}')
        
        return res

    @staticmethod
    def _td(*a,**k): return NotImplemented

    def try_resolve_op_1_to_many(self,left,right,op,chain_mode:str):
        res = getattr(right,f'_m_{op}_',self._td)(right,chain_mode)
        return res

    def try_resolve_op_many_to_1(self,left,right,op,chain_mode:str):
        res = getattr(right,f'_m_r_{op}_',self._td)(left,chain_mode)
        return res

    def try_resolve_op_1_to_1(self,left,right,op, loud=False):
        ''' Loud or Quiet evaluation of 1 to 1 shadow dunder methods for left._op_ and right._r_op_ '''

        res = getattr(left,f'_{op}_',self._td)(right)
        if not (res is NotImplemented): return res
        res = getattr(right,f'_r_{op}_',self._td)(left)
        if not (res is NotImplemented): return res
        else:    return NotImplemented

    def __repr__(self):
        return f'<Op Handler object: {self._desc} >'
    
    @property
    def _desc(self):
        return f'{self.left} --[{self.op}]--> {self.right}'
    
    @property
    def _expected_shape():
        #Text for expected shape errors
        ...

class _op_elem_mixin:
    ''' All subclasses generate an operational handler and return the result '''
    zip_flag : bool = False  
    dir_flag : str  = 'pos'

    def __invert__(self): self.zip_flag = True
    def __pos__(self): self.dir_flag = 'pos'
    def __neg__(self): self.dir_flag = 'neg'



def _make_dunder(name_root)->dict[FunctionType]:
    name = name_root
    def f(self,other):
        return operation_handler(self,other,name_root,is_root=True).resolve()        

    def f_inclusionary(self,other):
        return operation_handler(self,other,'i'+name_root,is_root=True).resolve()
    
    def f_reverse(self,other):
        return operation_handler(other,self,'r'+name_root,is_root=True).resolve()

    def f_reverse_inclusionary(self,other):
        return operation_handler(other,self,'ri'+name_root,is_root=True).resolve()
        ...
    return {
        f'__{name_root}__'  : f,
        f'__i{name_root}__' : f_inclusionary,
        f'__r{name_root}__' : f_reverse,
        f'__ir{name_root}__': f_reverse_inclusionary,
        }

def _make_dunders_all()->dict:
    _ops = ['add', 'sub', 'mul', 'truediv', 'mod', 'floordiv', 'pow', 'matmul', 'and', 'or', 'xor', 'rshift', 'lshift',]
    res  = {}
    for x in _ops: res|_make_dunder(x)
    return res

_op_elem_mixin = type('_op_elem_mixin',(_op_elem_mixin,),_make_dunders_all())


class object_set(_op_elem_mixin):
    ''' Generic set, which can intake multiple items 
    Unpacks other object_sets 
    '''
    
    items : list[item.node | item.socket]

    def __init___(self, *args,dedup=True):
        items = []

        for item in args:
            if isinstance(self,object_set):
                items.extend(*item)
            else:
                items.append(item)

        if dedup:
            self.items = list(iter_unseen(items))
        else:
            self.items = items

    Projection_Types = ['chain' , 'zip']
    def project(self, mode:str, left:op_elem):
        #TODO: 
        #TODO: Ensure left of particular shape
        assert mode in self.Projection_Types
        raise NotImplementedError('TODO PROJECTION TYPES') 

    def zip_project(self, left:op_elem):
        raise NotImplementedError('TODO PROJECTION TYPES') 

    def chain_project(self, left:op_elem):
        raise NotImplementedError('TODO PROJECTION TYPES') 

    def __getitem__(self,key:int|str|slice|Type):
        #TODO: Needs some logic work tbh, uncertain.
        if   isinstance(key,(int,slice)): return self.items[key]
        
        elif issubclass(item.node)  : 
            return [x for x in self.items if isinstance(x,key)] 
        
        elif isinstance(key,int)  : 
            return self.items[key] 
        elif isinstance(key,str)  : 
            return [x for x in self.items if getattr(x,'name') == key] 
        
        elif issubclass(item.socket):
            res1 = [x[key] for x in self.items if isinstance(x, sslice_keys)] 
            res2 = [x      for x in self.items if isinstance(x, key)]
            return socket_slice(*res1,*res2)
        elif isinstance(key,tuple):
            res1 = [x[key] for x in self.items if isinstance(x, sslice_keys)] 
            if isinstance(key[1],str):
                res2 = [x for x in self.items if key[1] == x.name]
            elif issubclass(item.socket):
                res2 = [x for x in self.items if isinstance(x, key[1])]
            else:
                res2 = []

            return object_set(*res1,*res2)

    @property
    def nodes(self):
        socketslice_res = [x.nodes for x in self.items if isinstance(x,socket_slice)]
        objectset_res   = [x.nodes for x in self.items if isinstance(x,object_set)  ]
        socket_res      = [x.context.node for x in self.items if issubclass(x.__class__,item.socket)  ]
        nodes_res       = [x      for x in self.items if issubclass(x.__class__,item.node)   ]
        
        res = []
        for x in socketslice_res:res.extend(x)
        for x in object_set     :res.extend(x)
        res.append(socket_res)
        res.append(nodes_res)
        return tuple(iter_unseen(res))

    def __iter__(self):
        for x in self.items: yield x

class socket_slice(_op_elem_mixin):
    def __init__(self,o:object_set,i:object_set,s:object_set):
        self.s_out  = o
        self.s_in   = i
        self.s_side = s
    
    @property
    def nodes(self)->tuple:
        #Determines all unqiue nodes from contained objects
        return tuple(iter_unseen(self.s,self.o,self.i))
            

    @property
    def s(self): return self.s_side
    @property
    def o(self): return self.s_out
    @property
    def i(self): return self.s_in

            
def _ensure_single_is_multi(item:object_set|tuple,Any):
    if not isinstance(item,(socket_slice,object_set,tuple)):
        return (item,)
    else:
        return item

class socket_mixin(_op_elem_mixin,_mixin.socket): 
    ...

class node_mixin(_op_elem_mixin,_mixin.node):
    def __iter__(self)->item.socket:
        for s in self.out_sockets:
            yield s
        
    def __getitem__(self, key:sslice_keys)->object_set|socket_slice:
        _dir = 'in out' #side is better suited for specific cases instead of generic 'in'
        _key = key
        single = False
        if isinstance(key,tuple):
            assert len(key) == 2
            _dir, _key = key
            
        if   _dir == 'out'  : return object_set(*_ensure_single_is_multi(self.out_sockets[_key])  )
        elif _dir == 'in'   : return object_set(*_ensure_single_is_multi(self.in_sockets[_key])   )
        elif _dir == 'side' : return object_set(*_ensure_single_is_multi(self.side_sockets[_key]) )
        
        else:
            if   _dir == 'out'  : _out  =  object_set(*_ensure_single_is_multi(self.out_sockets[_key])) 
            elif _dir == 'in'   : _in   =  object_set(*_ensure_single_is_multi(self.in_sockets[_key]))  
            elif _dir == 'side' : _side =  object_set(*_ensure_single_is_multi(self.side_sockets[_key]))
                #FUGLY, would be much better on the object set 
            return socket_slice(o=_out,i=_in,s=_side)

