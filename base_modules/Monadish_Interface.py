# from .utils.statics         import get_data_uuid, get_file_uid, INVALID_UUID
# from ..statics              import _unset
from ..models.struct_module import module, module_test
from ..models.base_node     import socket_group
from .Execution_Types       import _mixin, item
from .Execution_Types       import socket_shapes as st
from typing                 import Self, TypeAlias,AnyStr,Type,

import itertools

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
    Ops_Directional   = ['ishift','ishift']
    Ops_Inv_Direction = {'irshift':'ishift'}
    
    def __init__(self,left,right,op,is_root=False):
        #TODO: Suboperations should have is_root as false
        #TODO: Order left, right, and op (filtered)
        ...

    def _ensure_objset_from_tuple(self,item):
        if isinstance(item,tuple):
            return object_set(*item)
            #TEST IF WAS OBJECT_SET
        return item
         
    def Resolve(self):
        ''' Currently written as only regular arithmatic ops '''
        left  = self._ensure_objset_from_tuple(self.left ) 
        right = self._ensure_objset_from_tuple(self.right)
        op    = self.op

        #TODO: Check special op for

        zip_flag = getattr(self.left,'zip_flag',False) or getattr(self.right,'zip_flag',False) 
        
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

    def __add__(self,other:op_elem)->op_elem:
        '''self + other : handled via operation_handler'''
        return operation_handler(self,other,'add',is_root=True).resolve()
    def __sub__(self,other:op_elem)->op_elem:
        '''self - other : handled via operation_handler'''
        return operation_handler(self,other,'sub',is_root=True).resolve()
    def __mul__(self,other:op_elem)->op_elem:
        '''self * other : handled via operation_handler'''
        return operation_handler(self,other,'mul',is_root=True).resolve()
    def __truediv__(self,other:op_elem)->op_elem:
        '''self / other : handled via operation_handler'''
        return operation_handler(self,other,'truediv',is_root=True).resolve()
    def __mod__(self,other:op_elem)->op_elem:
        '''self % other : handled via operation_handler'''
        return operation_handler(self,other,'mod',is_root=True).resolve()
    def __floordiv__(self,other:op_elem)->op_elem:
        '''self // other : handled via operation_handler'''
        return operation_handler(self,other,'floordiv',is_root=True).resolve()
    def __pow__(self,other:op_elem)->op_elem:
        '''self ** other : handled via operation_handler'''
        return operation_handler(self,other,'pow',is_root=True).resolve()
    def __matmul__(self,other:op_elem)->op_elem:
        '''self @ other : handled via operation_handler'''
        return operation_handler(self,other,'matmul',is_root=True).resolve()
    def __and__(self,other:op_elem)->op_elem:
        '''self & other : handled via operation_handler'''
        return operation_handler(self,other,'and',is_root=True).resolve()
    def __or__(self,other:op_elem)->op_elem:
        '''self | other : handled via operation_handler'''
        return operation_handler(self,other,'or',is_root=True).resolve()
    def __sor__(self,other:op_elem)->op_elem:
        '''self ^ other : handled via operation_handler'''
        return operation_handler(self,other,'xor',is_root=True).resolve()
    def __rshift__(self,other:op_elem)->op_elem:
        '''self >> other : handled via operation_handler'''
        return operation_handler(self,other,'rshift',is_root=True).resolve()
    def __lshift__(self,other:op_elem)->op_elem:
        '''self << other : handled via operation_handler'''
        return operation_handler(self,other,'lshift',is_root=True).resolve()

    def __iadd__(self,other:op_elem)->op_elem:
        '''self += other : handled via operation_handler'''
        return operation_handler(self,other,'iadd',is_root=True).resolve()
    def __isub__(self,other:op_elem)->op_elem:
        '''self -= other : handled via operation_handler'''
        return operation_handler(self,other,'isub',is_root=True).resolve()
    def __imul__(self,other:op_elem)->op_elem:
        '''self *= other : handled via operation_handler'''
        return operation_handler(self,other,'imul',is_root=True).resolve()
    def __itruediv__(self,other:op_elem)->op_elem:
        '''self /= other : handled via operation_handler'''
        return operation_handler(self,other,'itruediv',is_root=True).resolve()
    def __imod__(self,other:op_elem)->op_elem:
        '''self %= other : handled via operation_handler'''
        return operation_handler(self,other,'imod',is_root=True).resolve()
    def __ifloordiv__(self,other:op_elem)->op_elem:
        '''self //= other : handled via operation_handler'''
        return operation_handler(self,other,'ifloordiv',is_root=True).resolve()
    def __ipow__(self,other:op_elem)->op_elem:
        '''self **= other : handled via operation_handler'''
        return operation_handler(self,other,'ipow',is_root=True).resolve()
    def __imatmul__(self,other:op_elem)->op_elem:
        '''self @= other : handled via operation_handler'''
        return operation_handler(self,other,'imatmul',is_root=True).resolve()
    def __iand__(self,other:op_elem)->op_elem:
        '''self &= other : handled via operation_handler'''
        return operation_handler(self,other,'iand',is_root=True).resolve()
    def __ior__(self,other:op_elem)->op_elem:
        '''self |= other : handled via operation_handler'''
        return operation_handler(self,other,'ior',is_root=True).resolve()
    def __isor__(self,other:op_elem)->op_elem:
        '''self ^= other : handled via operation_handler'''
        return operation_handler(self,other,'ixor',is_root=True).resolve()
    def __irshift__(self,other:op_elem)->op_elem:
        '''self >>= other : handled via operation_handler'''
        return operation_handler(self,other,'irshift',is_root=True).resolve()
    def __ilshift__(self,other:op_elem)->op_elem:
        '''self <<= other : handled via operation_handler'''
        return operation_handler(self,other,'ilshift',is_root=True).resolve()
    ...

class object_set(_op_elem_mixin):
    ''' Generic set, which can intake multiple items 
    Unpacks other object_sets 
    '''
    
    items : list[item.node | item.socket]

    def __init___(self, *args):
        items = []

        for item in args:
            if isinstance(self,object_set):
                items.extend(*item)
            else:
                items.append(item)

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

    def __getitem__():
        
        ...

class socket_slice(_op_elem_mixin):
    def __init__(self,o:object_set,i:object_set,s:object_set):
        self.s_out  = o
        self.s_in   = i
        self.s_side = s
        
    @property
    def s(self): return self.s_side
    @property
    def o(self): return self.s_out
    @property
    def i(self): return self.s_in

    def extend():
        #used in & operations between self types.
        #If between object_set & socket_slice, subsumed into object set. Projection of operations should still take care of that
        ...

            
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

