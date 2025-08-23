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

_ALL_OPS = ('add', 'sub', 'mul', 'truediv', 'mod', 'floordiv', 'pow', 'matmul', 'and', 'or', 'xor', 'rshift', 'lshift','radd', 'rsub', 'rmul', 'rtruediv', 'rmod', 'rfloordiv', 'rpow', 'rmatmul', 'rand', 'ror', 'rxor', 'rrshift', 'rlshift','iadd', 'isub', 'imul', 'itruediv', 'imod', 'ifloordiv', 'ipow', 'imatmul', 'iand', 'ior', 'ixor', 'irshift', 'ilshift','iradd', 'irsub', 'irmul', 'irtruediv', 'irmod', 'irfloordiv', 'irpow', 'irmatmul', 'irand', 'iror', 'irxor', 'irrshift', 'irlshift',)
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

current_patch_inst : 'Patches' = ContextVar('current_patch_inst', default=None)

@contextmanager
def context_current_patch(item:'Patches'):
    if item is None:
        yield
    else:
        t = current_patch_inst.set(item)
        yield
        current_patch_inst.reset(t)

#endregion


######## DUNDER MIXINS GENERATION ########
#region 

def resolve_operation_in_context(*args,**kwargs):
    return current_patch_inst.get().resolve_operation(*args,**kwargs)

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
        return resolve_operation_in_context(self,other,name_root)        

    def f_inclusionary(self,other):
        return resolve_operation_in_context(self,other,'i'+name_root)
    
    def f_reverse(self,other):
        return resolve_operation_in_context(other,self,'r'+name_root)

    def f_reverse_inclusionary(self,other):
        return resolve_operation_in_context(other,self,'ri'+name_root)
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

#endregion


######## MODULE MIXINS ########
#region


def _default_dict_true(dict):
    def __missing__(self,key):
        return True
def _default_dict_dict(dict):
    def __missing__(self,key):
        var = {}
        self[key] = var
        return var


class graph_mixin(_mixin.graph):
    @contextmanager
    def Monadish_Env(self, 
                     auto_add_nodes    = True, 
                     auto_add_links    = True, 
                     auto_delete       = True, 
                     auto_merge_target = None,
                     op_env            = None
                     ):
        ''' Creates a temporary subgraph that alllows auto-merging with base graph & a patch/operating env for resolving arithmatic symbol ops '''
        with context_current_patch(op_env):
            subgraph = self.subgraphs.new(key='Monadish_Env')
            with subgraph.As_Env(auto_add_nodes=auto_add_nodes,
                                 auto_add_links=auto_add_links):
                yield subgraph
            if auto_merge_target:
                auto_merge_target.copy_in_nodes(nodes = subgraph.nodes, keep_links = True, filter = subgraph.Monadish_Context_Item_Enabled)
            if auto_delete:
                self.subgraphs.free(subgraph)


class node_collection_mixin(_mixin.node_collection):
    @hook(event='new_item', mode='post')
    def _hook_special_monadish(self,item):
        ''' Ensure that a node added inside of a context sets the correct flags for actions that modify the graph to do so in a context not submitted to the main graph '''
        sg = item.context.subgraph
        if ck := getattr(sg,'_monadish_context_key_',None):
            if (k:=ck.get()) != ('main',):
                sg._monadish_special_context[k[-1]][item] = True
                sg._monadish_special_context[k[ 0]][item] = False


class subgraph_mixin(_mixin.subgraph):
    _monadish_special_context_ : _default_dict_dict
    _monadish_context_key_     : ContextVar         

    def _monadish_ensure_sc_(self):
        ''' Ensure special context variables are placed'''
        if not hasattr(self,'_monadish_special_context_'):
            self._monadish_special_context_         = _default_dict_dict()
            self._monadish_special_context_['base'] = _default_dict_true()
        if not hasattr(self,'_monadish_context_key_'):
            self._monadish_context_key_ = ContextVar(f'{self.name}_context_key', default=('base',))
            
    def Monadish_Merge_Contexts(self,key1,key2):
        ''' Merge into key1 '''
        a = self._monadish_special_context_[key1]
        b = self._monadish_special_context_[key2]
        self._monadish_special_context_[key1] = b|a

    def Monadish_Context_Item_Enabled(self,item)->bool:
        if not issubclass(item,item.node): 
            return True
        for k in self._monadish_context_key_.get():
            res = self._monadish_special_context_.get()[k][item]
            if res is not None: 
                return res
        raise Exception('Missing "base" key ')

    @contextmanager
    def Monadish_Temp(self, key:str):
        ''' Contexts exist as a diff against the contexts, thus nested context's just iterate over keys
        To merge contexts, use Monadish_Merge_Contexts '''
        
        self._monadish_ensure_special_context_()
        ck = self._monadish_context_key_
        assert key not in ck.get()
        current_context_value = ck.get()
        c = current_context_value + (key,)
        t = ck.set(c)

        yield key

        ck.reset(t)


class socket_collection_mixin(_mixin.socket_collection):
    def _monadish_unused_socket_groups(self,claimed_groups:list[socket_group]=None):
        ''' Yield unused potential from structural definition & add number of times cls apears in claimed arg'''

        if claimed_groups is None: claimed_groups = []

        for potential_group in self.Groups:
            max_inst = potential_group.SocketGroup_Quantity_Max
            inst_current_or_claimed =  len([x for x in self.groups if (isinstance(x, potential_group))])
            inst_current_or_claimed =+ len([x for x in self.groups if (x in claimed_groups)])
            if max_inst < inst_current_or_claimed:
                yield potential_group


#### Adding dunder methods mixins ####
class sg_mixin(_op_elem_mixin,_mixin.socket_group):...
class socket_mixin(_op_elem_mixin,_mixin.socket):...
class node_mixin(_op_elem_mixin,_mixin.node):...


main._loader_mixins_ = [
    graph_mixin,
    subgraph_mixin,
    socket_collection_mixin,
    sg_mixin,
    socket_mixin,
    node_mixin,
    ]

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

    @classmethod
    def wrapper(cls,
                 patches : 'Patches',
                 operation      :Any|str|tuple[str]  = None       ,
                 but            :str|tuple|None      = None       ,
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
                       but            = but,
                       mode           = mode,
                       key            = key,
                       allow_fallback = allow_fallback,
                       filter         = filter,
                       safe           = safe)
            patches.intake_operation(inst)
            return inst
        return wrapper

    def __init__(self, 
                 func           :FunctionType|Self                ,
                 operation      :Any|str|tuple[str]  = None       ,
                 op             :Any|str|tuple[str]  = None       ,
                 but            :str|tuple|None      = None       ,
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
        if but:
            if isinstance(but,str)     : but = (but,)
            operation = tuple((x for x in operation if x not in but))

        self.func           = func
        self.operations     = operation
        self.mode           = mode
        self.key            = key
        self.allow_fallback = allow_fallback
        self.filter         = filter
        self.safe           = safe

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
        if   op == 'lshift'  : op = 'rshift'
        elif op == 'ilshift' : op = 'irshift'
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
        if   op == 'lshift'  : op = 'rshift'
        elif op == 'ilshift' : op = 'irshift'
        return (op,sg,r,l) + args, kwargs

    @operation(patches,Any)
    def return_right(cls,op,sg,l,r,*args,**kwargs):
        return r


class _tests:
    @dp_wrap(0)
    def automerge_test(graph,subgraph):
        ''' Test if auto_merge_target works '''
        with graph.Monadish_Env(auto_merge_target = subgraph) as _sg:
            left  = node_left_simple_1(default_sockets=True)
            assert subgraph is not _sg
            assert left.context.subgraph is _sg
        # assert left.copied_to[subgraph].context.subgraph is subgraph
        assert subgraph.nodes[0].UID == left.UID

    @dp_wrap(0)
    def loading_patches_test(graph,subgraph):
        ''' Test if patches are loaded correctly '''
        with graph.Monadish_Env(op_env = _test_patch_simple.patches):
            left  = node_left_simple_1(default_sockets=True)
            right = node_right_simple_1(default_sockets=True)

            assert right is (left >> right)
            assert left  is (left << right)
            assert right is (left +  right)

    @dp_wrap(0)
    def temp_env_test(graph,subgraph):
        ''' Test walk rules in special env layers '''
        with graph.Monadish_Env(op_env = default_patches.patches) as _sg:
            left  = node_left_simple_1(default_sockets=True)

            with _sg.Monadish_Temp():
                right = node_right_simple_1(default_sockets=True)
                assert right not in _sg.env['base']
                #TODO: NOT CORRECT METHOD OF VERIFYING
            
            subgraph.merge_in_walk(right)

    @dp_wrap(0)
    def temp_env_fork_test(graph,subgraph):
        ''' Test forking of mutating operations within a temp env '''
        with graph.Monadish_Env(op_env = default_patches.patches) as _sg:
            left  = node_left_simple_1(default_sockets=True)
            right = node_right_simple_1(default_sockets=True)

            with _sg.Monadish_Temp():
                new_right = left >> right
                #Mutating operations fork affected items.
            assert new_right != right


    @dp_wrap(0)
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
                               'Core_Execution':'2.0', 
                               'Operations'    :'1.0'}, 
                funcs       = [
                                _tests.automerge_test           ,
                                # _tests.loading_patches_test     ,
                                # _tests.temp_env_test            ,
                                # _tests.temp_env_fork_test       ,
                                # _tests.temp_env_with_delay_test ,
                              ],
                ))

#endregion

