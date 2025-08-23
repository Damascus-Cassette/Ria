''' Atomic recursion-operation monadish, to allow for dev override and use of env 
Yeah, it's overkill :D
'''

from ..models.struct_module    import module, module_test
from ..models.base_node        import socket_group
from .Execution_Types          import _mixin, item
from ..models.struct_hook_base import hook
from .utils.print_debug import (debug_print_wrapper as dp_wrap, 
                                _debug_print        as dprint ,
                                debug_level                   , 
                                debug_targets                 ) 

from types       import LambdaType,GeneratorType,FunctionType
from contextlib  import contextmanager
from inspect     import isgenerator
from contextvars import ContextVar
from typing      import Any,Self
from functools   import partial
from copy        import copy

_ORDER   = [] #For verifying that (project returns downwards on at least one item) and (preprocess doesnt move things upwards) 

_ALL_OPS = ('add', 'sub', 'mul', 'truediv', 'mod', 'floordiv', 'pow', 'matmul', 'and', 'or', 'xor', 'rshift', 'lshift','radd', 'rsub', 'rmul', 'rtruediv', 'rmod', 'rfloordiv', 'rpow', 'rmatmul', 'rand', 'ror', 'rxor', 'rrshift', 'rlshift',)
    #Not ugly at all...


######## MODULE HEADER ########
#region
class main(module):
    ''' A monad-like interface for creating node trees using contextual envs as req '''
    UID     = 'Monadish_Interface'
    Version = '1.2'

#endregion


######## ENV VARIABLES ########
#region 

current_patch_inst = ContextVar('current_patch_inst', default=None)

#endregion


######## MODULE MIXINS ########
#region


#endregion


######## MODULE ITEMS ########
#region

class _delay:... #Utility identifier class

class delay_mutable(_delay):
    ''' TODO: a slice/socket or similar used on the delay node
    passes creation arguments to be used in resolving a delay '''

class delay_node(item.node,_delay):
    ''' TODO: A node that intakes operations into a delay, 
    re-applies them to the acting as node 
    Will require adjustments to safeties around sockets & similar '''
    is_resolved : bool
    operations  : list 
    acting_node : item.node

    def resolve_delayed():
        ... #TODO

    def append_operation(op,sg,l,r, patches):
        ... #TODO

main._loader_items_.extend([
    delay_node,
    ])


#endregion


######## OPERATION OBJ & WRAPPER ########
#region

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

#endregion


######## OPERATION CONTAINER BASE TYPES ########
#region

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
        
#endregion


######## DEFAULT OPERATION CONTAINER ########
#region

class default_patches:
    ''' Simpler example for time, only a few operations. Nothing deeply recursive. Meant to be only (node --op--> node) which projects to (sg --op--> sg) where left must be fullfilled & right can accomidate with potential sg s '''

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
        ''' Project operation in a zip fashion, returns a lambda that undoes zip_flag and does operation 
        projection must return LambdaType that resolves action and casts type to correct group 
        In this module it will project sg -> sg & potential_sg '''
        #TODO

#endregion


######## TEST-ONLY ITEMS ########
#region

class _m():
    Module  = main 
    Label   = 'test_item'
    Version = '1.0'
    ...

class a_socket(_m,item.socket):
    UID        = 'Test_MonadSocket_A'

    Value_In_Types    = str
    Value_Out_Type    = str
    Value_Default     = 'c'

class b_socket(_m,item.socket):
    UID        = 'Test_MonadSocket_B'

    Value_In_Types    = int
    Value_Out_Type    = int
    Value_Default     = 'c'

class c_socket(_m,item.socket):
    UID        = 'Test_MonadSocket_C'

    Value_In_Types    = (int,str)
    Value_Out_Type    = str
    Value_Default     = 'c'

class a_socket(_m,item.socket):
    UID        = 'Test_MonadSocket_A'

    Value_In_Types    = str
    Value_Out_Type    = str
    Value_Default     = 'c'

class b_socket(_m,item.socket):
    UID        = 'Test_MonadSocket_B'

    Value_In_Types    = int
    Value_Out_Type    = int
    Value_Default     = 'c'

class c_socket(_m,item.socket):
    UID        = 'Test_MonadSocket_C'

    Value_In_Types    = (int,str)
    Value_Out_Type    = str
    Value_Default     = 'c'

class node_a1_a1(_m,item.exec_node):
    UID     = 'node_a1_a1'

    in_sockets    = [socket_group.construct('set_a', Sockets=[a_socket])]
    out_sockets   = [socket_group.construct('set_a', Sockets=[a_socket])]
    # side_sockets  = [socket_group.construct('set_a', Sockets=[a_socket])]

class node_b1_b1(_m,item.exec_node):
    UID     = 'node_b1_b1'
    in_sockets    = [socket_group.construct('set_a', Sockets=[b_socket])]
    out_sockets   = [socket_group.construct('set_a', Sockets=[b_socket])]

class node_c1_c1(_m,item.exec_node):
    UID     = 'node_c1_c1'
    in_sockets    = [socket_group.construct('set_a', Sockets=[c_socket])]
    out_sockets   = [socket_group.construct('set_a', Sockets=[c_socket])]

class node_left_simple_1(_m,item.exec_node):
    UID     = 'node_left_simple_1'
    in_sockets   = []
    side_sockets = []
    out_sockets  = [socket_group.construct('side_a', Sockets=[a_socket,
                                                               c_socket]),
                    socket_group.construct('side_a', Sockets=[b_socket])]

class node_right_simple_1(_m,item.exec_node):
    UID     = 'node_right_simple_1'
    side_sockets = []
    out_sockets  = []
    in_sockets   = [socket_group.construct('side_b1', Sockets=[a_socket,
                                                               c_socket]),
                    socket_group.construct('side_b2', Sockets=[b_socket])]

main._loader_items_.extend([
    a_socket            ,
    b_socket            ,
    c_socket            ,
    node_a1_a1          ,
    node_b1_b1          ,
    node_c1_c1          ,
    node_left_simple_1  ,
    node_right_simple_1 ,
    ])

#endregion


######## TESTS ########
#region

class _test_patch_simple():
    patches = Patches()

    @operation(patches, op = ('lshift','ilshift'), mode = 'preprocess')
    def logical_direction(cls, op,sg,l,r, *args, **kwargs):
        ''' PreProcess: Switch logical direction with above ops '''
        if op is   'lshift'  : op = 'rshift'
        elif op is 'ilshift' : op = 'irshift'
        return (op,sg,r,l) + args, kwargs

    @operation(patches,Any)
    def return_right(cls,op,sg,l,r,*args,**kwargs):
        return r


class _tests:
    @dp_wrap(threshold = 0)
    def automerge_test(graph,subgraph):
        ''' Test if auto_merge_target works '''
        with graph.Monadish_Env(auto_merge_target = subgraph) as _sg:
            left  = node_left_simple_1(default_sockets=True)
            assert subgraph is not _sg
            assert left.subgraph is _sg
        assert left.subgraph is subgraph

    @dp_wrap(threshold = 0)
    def loading_patches_test(graph,subgraph):
        ''' Test if patches are loaded correctly '''
        with graph.Monadish_Env(op_env = _test_patch_simple.patches):
            left  = node_left_simple_1(default_sockets=True)
            right = node_right_simple_1(default_sockets=True)

            assert right is (left >> right)
            assert left  is (left << right)
            assert right is (left +  right)

    @dp_wrap(threshold = 0)
    def temp_env_test(graph,subgraph):
        ''' Test walk rules in special env layers '''
        with graph.Monadish_Env(op_env = default_patches.patches) as _sg:
            left  = node_left_simple_1(default_sockets=True)
            left >> right

            with _sg.Monadish_Temp():
                right = node_right_simple_1(default_sockets=True)
                assert right not in _sg.env['base']
                #TODO: NOT CORRECT METHOD OF VERIFYING
                   
            subgraph.merge_in_walk(right)

    @dp_wrap(threshold = 0)
    def temp_env_with_delay_test(graph,subgraph):
        ''' Test delay in env '''
        with graph.Monadish_Env(op_env = default_patches.patches) as _sg:
            left  = node_left_simple_1(default_sockets=True)
            right = delay_node(default_sockets=True)
            left >> right

            with _sg.Monadish_Temp():
                real_right_node = node_right_simple_1(default_sockets=True)
                right @= real_right_node
                subgraph.merge_in_walk(right)

        assert len(subgraph.nodes) == 2
        assert real_right_node.label in subgraph.nodes.keys()
        assert not right.label in subgraph.nodes.keys()
        

main._module_tests_.append(module_test('TestA',
                module      = main,
                module_iten = {main.UID : main.Version,
                               'Core_Execution':'2.0'}, 
                funcs       = [
                                _tests.automerge_test           ,
                                # _tests.loading_patches_test     ,
                                # _tests.temp_env_test            ,
                                # _tests.temp_env_with_delay_test ,
                              ],
                ))

#endregion
