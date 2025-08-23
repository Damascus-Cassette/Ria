from contextvars import ContextVar
from typing      import Any,Self
from types       import LambdaType,GeneratorType,FunctionType
from inspect     import isgenerator
from copy import copy

_ORDER   = [] #For verifying that (project returns downwards on at least one item) and (preprocess doesnt move things upwards) 

_ALL_OPS = ('add', 'sub', 'mul', 'truediv', 'mod', 'floordiv', 'pow', 'matmul', 'and', 'or', 'xor', 'rshift', 'lshift','radd', 'rsub', 'rmul', 'rtruediv', 'rmod', 'rfloordiv', 'rpow', 'rmatmul', 'rand', 'ror', 'rxor', 'rrshift', 'rlshift',)
    #Not ugly at all...

from functools import partial
from contextlib import contextmanager
class _operation():
    siblings:list[Self]

    @staticmethod
    def wrapper(cls,patches : 'Patches',
                 operation      :Any|str|tuple[str]  = None       ,
                 op             :Any|str|tuple[str]  = None       ,
                 mode           :str                 = 'operation', 
                 key            :str|None            = None       , 
                 allow_fallback :bool                = False      , 
                 filter         :bool|LambdaType     = True       , 
                 safe           :bool                = True):
        #TODO: Figure out how to insert class into this!
        def wrapper[T](func:T)->T:
            inst =  cls(func = func,
                       operation      = operation,
                       op             = op,
                       mode           = mode,
                       key            = key,
                       allow_fallback = allow_fallback,
                       filter         = filter,
                       safe           = safe)
            patches.append_operation(inst)
            return inst
        return wrapper

    def __init__(self, 
                 func           :FunctionType|Self                ,
                 operation      :Any|str|tuple[str]  = None       ,
                 op             :Any|str|tuple[str]  = None       ,
                 mode           :str                 = 'operation', 
                 key            :str|None            = None       , 
                 allow_fallback :bool                = False      , 
                 filter         :bool|LambdaType     = True       , 
                 safe           :bool                = True):
        assert mode in ('preprocess', 's_operation', 'operation', 'project')

        if operation is None: 
            assert op 
            operation = op

        if isinstance(func,_operation):
            self.siblings = func.siblings
            self.siblings.append(self)
            func = func.func
        else:
            self.siblings = []

        if operation is Any            : operation = _ALL_OPS
        elif isinstance(operation,str) : operation = (operation,)
        else                           : assert isinstance(operation,(tuple,list,set))
        
        self.func           = func
        self.operations     = operation
        self.mode           = mode
        self.key            = key
        self.allow_fallback = allow_fallback
        self.filter         = filter
        self.safe           = safe
        self.cast_to        = cast_to

    def match(self,*args,**kwargs):
        if isinstance(self.filter, LambdaType):
            return self.filter(*args,**kwargs)
        assert isinstance(self.filter, bool)
        return self.filter

    # def __get__(self,inst,inst_cls):
    #     return partial(self,inst_cls)
    # may will prevent me from accessing the rest of this instance

    def __call__(self,*args,**kwargs):
        match self.mode:
            case 'preprocess' :
                return self.run_as_prep(*args,**kwargs)
            case 's_operation' :
                return self.run_as_sop(*args,**kwargs)
            case 'operation' :
                return self.run_as_op(*args,**kwargs)
            case 'project' :
                return self.run_as_project(*args,**kwargs)
        raise Exception('Out of bounds') 

    def run_as_prep(self,*args,**kwargs):
        ''' preprocesses format inputs, thus they must return all args '''
        return self.func(*args,**kwargs)
    
    def run_as_sop(self,*args,**kwargs)->LambdaType|Any:    
        ''' Regular operation that has a garunteed higher priority in resolution
        Returns either Lambda or object(node/socket/ect) '''
        return self.func(*args,**kwargs)

    def run_as_op(self,*args,**kwargs)->LambdaType|Any: 
        ''' Regular operation
        Returns either Lambda or object(node/socket/ect) '''
        return self.func(*args,**kwargs)
    
    def run_as_project(self,*args,**kwargs)->LambdaType: 
        ''' iterate through projects, return lambda that resolves action '''
        res = self.func(*args,**kwargs)
        assert isinstance(res,LambdaType)
        return res
    
    # def run_as_project(self,*args,**kwargs)->LambdaType:
    #     #TODO: Evalute in a way that asserts higher->lower order.
    #     # Do via returning projected items and handling indv lambda creation here?
        
    #     assert isgenerator(self.func)
    #     gen = self.func(*args,**kwargs) 
    #     res = []
    #     for item in gen:
    #         if not item:
    #             return False
    #         res.append(item)
    #     return lambda *args,**kwargs: self.cast_to([x(*args,**kwargs) for x in item])
    
operation = _operation.wrapper

class _patches_item_list(list):
    def __iter__(self):
        seen_keys = []
        for x in super().__iter__:
            x:_operation
            k = x.key
            if not x.allow_fallback:
                break
            if k and k in seen_keys:
                continue
            elif k:
                seen_keys.append(k)
            yield x
        return StopIteration


class _patches_type_mode(dict):
    def __missing__(self,key):
        self[key] = ls = _patches_item_list()
        return ls

    def __or__(self,other:Self):
        ''' Right priority merge/replace by key '''
        if not isinstance(other,Patches): return NotImplemented
        new = _patches_type_mode
        for k,v in other.items():
            new[k]=copy(v)
        for k,v in self.items():
            if k not in other.keys():
                new[k]=copy(v)


    def __and__(self,other:Self):
        if not isinstance(other,Patches): return NotImplemented
        ''' Right priority append '''
        new = _patches_type_mode
        for k,v in other.items():
            new[k].extend(v)
        for k,v in self.items():
            new[k].extend(v)

class Patches():
    ''' mergable data-Struct containing default of dict[mode]=[each_item] (Skips over matching keys, respects block)'''
    ''' Basically an operation Handler instance now it's evolved '''
    def __init__(self):
        self.preprocess  = _patches_type_mode()
        self.s_operation = _patches_type_mode()
        self.operation   = _patches_type_mode()
        self.project     = _patches_type_mode()
    
    def __call__(self,cls,op,sg,l,r):
        self.temp_item_env(sg)
        
        res = self.resolve_operation(cls,op,sg,l,r)
        if res: 
            result =  res()
            self.temp_item_env_close()
            return result
        else:
            self.temp_item_env_cancel()
            raise Exception(f'COULD NOT RESOLVE LR AND OP! {l} --{op}--> {r}')

    

    def temp_item_env_open(subgraph):
        ''' Create a temporary env to place new nodes in, then free after completion '''
        #Set env
        yield
        #merge if applied
        #free  if unused
        ...

    def resolve_operation(self,cls,op,*args,**kwargs)->LambdaType|None:
        ''' prep resolve operation via order of operations, if operation is possible returns a lambda that resolves head operation'''
        x:_operation
        for x in self.preprocess[op]:
            if x.match(cls,op,*args,**kwargs):
                (op,*args), kwargs =x(cls,op,*args,**kwargs)
                    
        for x in self.s_operation[op]:
            if x.match(cls,op,*args,**kwargs):
                if res:=x(cls,op,*args,**kwargs):
                    return res

        for x in self.operation[op]:
            if x.match(cls,op,*args,**kwargs):
                if res:=x(cls,op,*args,**kwargs):
                    return res

        for x in self.project[op]:
            if x.match(cls,op,*args,**kwargs):
                if res:=x(cls,op,*args,**kwargs):
                    return res

    def intake_operation(self,oper:_operation):
        for _op in oper.operations:
            getattr(self,oper.mode)[_op].append(oper)
    

    def __or__(self,other:Self)->Self:
        ''' Creates new object with right priority. Replaces operation chains on the right '''
        if not isinstance(other,Patches): return NotImplemented
        new = Patches.__new__()
        new.preprocess  = self.preprocess  | other.preprocess   
        new.s_operation = self.s_operation | other.s_operation 
        new.operation   = self.operation   | other.operation   
        new.project     = self.project     | other.project     
        return new
    
    def __add__(self,other:Self)->Self:
        ''' Creates new object with right priority. Extends left operations on the right'''
        if not isinstance(other,Patches): return NotImplemented
        new = Patches.__new__()
        new.preprocess  = self.preprocess  + other.preprocess   
        new.s_operation = self.s_operation + other.s_operation 
        new.operation   = self.operation   + other.operation   
        new.project     = self.project     + other.project     
        return new
        
current_patch_inst = ContextVar('current_patch_inst', default=None)

class default_patches:
    ''' Simpler example for time, only a few operations. Nothing deeply recursive. Meant to be only (node --op--> node) which projects to (sg -op> sg) '''

    patches = Patches()

    @operation(patches, op = ('lshift','ilshift'), mode = 'preprocess')
    def logical_direction(cls, op,sg,l,r, *args, **kwargs):
        ''' PreProcess: Switch logical direction with above ops '''
        if op is   'lshift'  : op = 'rshift'
        elif op is 'ilshift' : op = 'irshift'
        return (op,sg,r,l) + args, kwargs
    
    @operation(patches, Any, but = 'imat', mode = 's_operation', filter= lambda sg,l,r: issubclass(l.__class__,_delay) or issubclass(r.__class__,_delay))
    def delay_node(cls, op,sg,l,r, *args, **kwargs):
        ''' A delayed item is one that isnt defined yet, but is used anyway. 
        When the node is replaced using the @= on it, it resolves all operations. 
        Nested delays are point to their contextual or perm replacement 
        Delays can be delayed nodes,sockets,slices, ect
        '''
        if issubclass(l.__class__,_delay): 
            l.append_operation(op,sg,l,r, patches = current_patch_inst.get())
        elif issubclass(r.__class__,_delay): 
            r.append_operation('r{op}',sg,l,r, patches = current_patch_inst.get())
        return r
    
    @operation(patches, 'imat', mode = 's_operation', filter= lambda sg,l,r: issubclass(l.__class__,_delay))
    def replace_delay(cls, op,sg,l,r, *args, **kwargs):
        ''' Replaces the delay item, which resolves all pending operations'''
        l.replace_with(r)
        return r
        
    @operation(patches, op = ('lshift','ilshift'), filter = lambda sg,l,r: isinstance(l,socket_group) or isinstance(r,socket_group))
    def operation_sg_sg_connect(cls, op,sg,l,r, *args, **kwargs):
        ''' TODO Apply the connection between socket groups'''
        ...

    @operation(patches, op = Any, mode = 'project', filter = lambda sg,l,r: all([issubclass(l.__class__,item.node),issubclass(r.__class__,item.node)]) and any([r.zip_flag, l.zip_flag]) )
    def project_zip_node(cls, op,sg,l,r, *args, **kwargs)->LambdaType:
        ''' Project operation in a zip fashion, returns a lambda that undoes zip_flag and does operation '''
        ''' projection must return LambdaType that resolves action and casts type to correct group '''
        ...

class second_level_patches:
    patches = Patches()
    ...

def test():
    assert b == (a >> b) 


