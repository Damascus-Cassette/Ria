from contextvars import ContextVar
from contextlib import contextmanager
monadish_op_env = ContextVar('monadish_op_env')

from functools import partial
from typing    import Any, Type, Self
from copy      import copy

lower_order  : tuple #Anything else of expected types
higher_order : tuple #(node_group, mixed_group)



class _operation():
    
    def __init__(self, 
                func                                            ,
                op                                              ,
                left_type  : Any|Type|tuple[Type] = lower_order ,
                right_type : Any|Type|tuple[Type] = lower_order ,
                either_match = False                            ,
                filter       = True                             ,):

        if isinstance(func,_operation):
            self._op_siblings = func._op_siblings
            self._op_siblings.append(self)
            func = func.func
        else:
            self._op_siblings = []
        
        if isinstance(op,str):
            op = (op,)

        self.func         = func
        self.ops          = op
        self.left_type    = left_type
        self.right_type   = right_type
        self.either_match = either_match
        self.filter       = filter

    def side_is_higher_order(self,side:str='left')->bool:
        ty = getattr(self,f'{side}_type')        
        if ty is Any or ty is higher_order: 
            return True
        elif isinstance(ty,(tuple,list,set)):
            return any([x for x in ty in higher_order])
        return False

    def order_catagory(self)->str:
        l = self.side_is_higher_order(side = 'left'  )
        r = self.side_is_higher_order(side = 'right' )
        if ((self.either_match and (l or r)) or (l and r)):
            return 'major_major'
        elif l or r:
            return 'major_minor'
        else:
            return 'minor_minor'

    def __get__(self,instance,container_cls):
        return partial(self,container_cls)

    def __call__(self,container_cls,*args,**kwargs):
        return self.func(container_cls,*args,**kwargs)

    # @contextmanager
    # def __enter__(self):
    #     'prep operations to monadish_op_env'
    #     # Add self.data to monadish_op_env
    #     yield
    #     # revert

def operation(patches, *args, **kwargs):
    def wrapper[T](func:T)->T:
        new =  _operation(func,*args,**kwargs)
        patches.append_operation(new)
        return new
    return wrapper


class patch_list(list):...


class patch_by_op(dict):
    def __missing__(self,key)->patch_list[_operation]:
        self[key] = ls = patch_list()
        return ls

    def __or__(self,other:Self):
        ''' Right (other) dominated union '''
        new = patch_by_op()
        _ks = list(self.keys())
        for k,v in self.items():
            new[k]=copy(v)
        for k,v in self.items():
            if k not in _ks:
                new[k]=copy(v)
        return new
    
    def __add__(self,other:dict|Self):
        ''' Returns a new instance who's child lists are extended from the other '''
        new = patch_by_op()
        for k,v in self.items():
            new[k]=copy(v)
        for k,v in self.items():
            new[k].extend(v)

    def search(self,op,subgraph,left,right)->_operation|None:
        for op_inst in self[op]:
            op_inst : _operation
            if op_inst.matches_filter(op,subgraph,left,right):
                return op

current_patches = ContextVar('current_patches', defult = None)


class Patches():
    major_major : patch_by_op
    major_minor : patch_by_op
    minor_minor : patch_by_op

    def __init__(self, 
                 add_major_major = False, #extend instead of merging  
                 add_major_minor = False, #  
                 add_minor_minor = False, #
                 empty           = False,
                ):
        ''' Create new patches instance
        :param add_major_major: extend this priority type during a merge | operation
        :param add_major_minor: extend this priority type during a merge | operation
        :param add_minor_minor: extend this priority type during a merge | operation
        '''
        if not empty:
            self.major_major = patch_by_op()
            self.major_minor = patch_by_op()
            self.minor_minor = patch_by_op()
        self.add_major_major = add_major_major
        self.add_major_minor = add_major_minor
        self.add_minor_minor = add_minor_minor

    #TODO: Below allow or disallow fallback is *very* primitive

    def __or__(self,other):
        if not isinstance(other,Patches): return NotImplemented
        ''' merge all Patches right, ie dont extend patch_lists for fallback '''
        new = Patches(other.add_major_major, other.add_major_minor, other.add_minor_minor,empty=True)
        if other.add_major_major: new.major_major = other.major_major + self.major_major
        else:new.major_major = self.major_major | other.major_major 
        if other.add_major_minor: new.major_minor = other.major_minor + self.major_minor
        else:new.major_minor = self.major_minor | other.major_minor 
        if other.add_minor_minor: new.minor_minor = other.minor_minor + self.minor_minor
        else:new.minor_minor = self.minor_minor | other.minor_minor 
        return new
    
    def __and__(self,other):
        ''' Add all patches right, extend to allow fallback behavior. Inherits rightmost's add settings '''
        new = patches(other.add_major_major, other.add_major_minor, other.add_minor_minor,empty=True)
        new.major_major = other.major_major + self.major_major
        new.major_minor = other.major_minor + self.major_minor
        new.minor_minor = other.minor_minor + self.minor_minor
        return new
    
    def search(self,op:str,subgraph,left,right)->_operation:
        ''' Find in priority series '''
        if res:=self.major_major.search(op,subgraph,left,right): return res
        if res:=self.major_minor.search(op,subgraph,left,right): return res
        if res:=self.minor_minor.search(op,subgraph,left,right): return res
        return NotImplemented
        
    def append_operation(self,op:_operation):
        cat = op.order_catagory()
        for _op in op.ops:
            getattr(self, cat)[_op].append(op)

    @contextmanager
    def as_env(self):
        t = current_patches.set(self)
        yield
        current_patches.reset(t)

if __name__ == '__main__':
    class sum_node():
        ...

    class patches_test_base():
        patches = Patches()

        @operation(patches, ops = ('rshift','irshift'), left_type=Any, right_type=Any, either_match=True)
        def reverse_logical(cls,op:str,subgraph,l,r):   
            op = op.replace('r','l')
            return handle_env_operation(op,subgraph,r,l)
            # return r
        
        @operation(patches, ops = ('shift','ishift'))
        def shift_in_logical(cls,op:str,subgraph,l,r):   
            return r

    def test_logical_inverse_patch(graph,subgraph):
        with subgraph.Monadish_Env(patches = patches_test_base) as _msg:
            l = new_node()
            r = new_node()
            assert r == l << r
            assert r == l >> r
            
            

