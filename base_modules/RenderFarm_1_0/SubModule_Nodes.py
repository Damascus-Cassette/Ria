from .Submodule_Tasking         import Memo
from .Data_Structures           import Backwards_Context
from ..Execution_Types          import item, _mixin, socket_shapes
from ..utils.print_debug        import debug_print_wrapper
from ...statics                 import _unset
from ...models.struct_hook_base import hook, hook_trigger
from ...models.struct_module    import module_test
from ...models.base_node        import (subgraph            as _subgraph_base,
                                        node_collection     as _node_collection_base,
                                        subgraph_collection as _subgraph_collection_base,)


from typing import Any
from contextvars import ContextVar
from contextlib  import contextmanager

#FEATURE REQ LIST:
# - [ ] Basic Execution
# - [ ] Structural state-sum
# - [ ] Value      state-sum
# x [ ] Flag Declaration for server caching  #DO IN ANOTHER SUB MODULE




######## SHARED MIXINS ########
#region

class socket_mixin(_mixin.socket):
    ''' Indv Value (in/side or out) in a unit of work. '''
    
    Value_Shape    : socket_shapes.single = socket_shapes.single 
        # Socket shape is determined by structure min-max in socket group's def, want to change to indv connections sometime 

    @property
    def memo_address(self)->str:
        c = self.context
        return '.'.join((c.node.uid, self.Direction, self.label)) 
    
    _value    : Any = _unset
        # In not-exec make this act a context reading dict that returns/sets values (default _unset)
        # value would then need to be registerd in forward downstreams context for that node to view properly?
        # last_value is bit of a lazy and hacky way to do it, but could work.

    @property
    def value(self):
        return self._value
    @value.setter
    def value(self,item):
        self._value = item


    exec_value : Any

    _has_executed       : bool = False
    _last_executed_with : str  = _unset

    @hook(event ='execute',mode='wrap', key = '_execute_caching_')
    def _execute_caching_(self,func):

        address = self.address
        memo    = active_job.get().memo
        if address+'.value' in memo.keys():
            return memo[address+'.value']

        state_key = self.get_state_key(self.subgraph.state)
            #Use same method for lazy invalidation?

        if self._has_executed and (self._last_execute_with is state_key):
            return self.exec_value
        
        res = func(state_key)

        self._has_executed       = True
        self._last_executed_with = state_key

        if res is not _unset:
            self.exec_value = res
            return res
        
        return self.Default_Value

    @hook_trigger('execute')
    def execute(self):
        links = [*self.links]
        
        if not len(links):
            return self.value

        #Fugly AS FUCK
        is_single = (self.Socket_Shape is socket_shapes.single) or (
                        (self.context.socket_group.Link_Limit == 1) and 
                        (self.Socket_Shape is socket_shapes.mutable)) 

        if is_single:
            return links[0].other(self).execute()
        else:
            res = []
            for link in links:
                node = link.other(self)
                res.append(node.execute())
            return res


    @hook(event ='compile',mode='wrap', key = '_compile_caching_')
    def _compile_caching_(self,func, exec_sugraph, backwards_context):
        
        address = self.address
        memo    = active_job.get().memo
        if address+'.value' in memo.keys():
            return memo[address+'.value']

        state_key = self.get_state_key(backwards_context)

        if (res:=self.value[state_key]) is not _unset:
            return res

        with backwards_context.checkin(self.memo_address):
            res = func(exec_sugraph, backwards_context, state_key)
        self.value[state_key] = res

    @hook_trigger('compile')
    def compile(self, exec_sugraph, backwards_context):
        links = [*self.links]
        
        if not len(links):
            return self.value

        #Fugly AS FUCK
        is_single = (self.Socket_Shape is socket_shapes.single) or (
                        (self.context.socket_group.Link_Limit == 1) and 
                        (self.Socket_Shape is socket_shapes.mutable)) 

        if is_single:
            return links[0].other(self).compile()
        else:
            res = []
            for link in links:
                node = link.other(self)
                res.append(node.compile())
            return res

    
    def get_context_components(self)->tuple[str,list[str]]:
        ''' get context componetns '''
        for link in self.links:
            other_node = link.other(self)
            other_node.
#endregion


######## EXEC MIXINS ########
#region


class exec_node_mixin(_mixin.exec_node):
    ''' Individual unit of work.
    Characterized by:
    - No backwards_context (?)
    - Requirement to be in exec_graph
    - Upstream state awareness (via walk and key)
    - Memo    Allowence
    - Caching Allowence
    '''

    # @hook(event='execute', mode='wrap', key='_exec_cache_')
    # def _exec_cache_(self, func, subgraph):
    #     func()

    @property
    def memo_address(self)->str:
        c = self.context
        return '.'.join([c.graph , 'EXEC' , self.label])

    @hook_trigger(event='execute')
    def execute(self,):
        raise NotImplementedError(f'Execute was not set on {self.UID}!') 


class exec_subgraph_mixin(_mixin.subgraph):
    active_memo : ContextVar

    @hook_trigger('execute')
    def execute(self, item_inst:item.exec_node|item.socket):
        item_inst.execute(self)


#endregion


######## META MIXINS ########
#region


class meta_node_mixin(_mixin.exec_node):
    ''' High level nodes that compile into an exec_graph '''

    @property
    def memo_address(self)->str:
        c = self.context
        return '.'.join([c.graph , c.subgraph , self.label])
    
    @hook_trigger('compile')
    def compile(self, exec_graph, backwards_context, context_state):
        raise NotImplementedError(f'Compile not implimented in node {self.UID}!')


class meta_subgraph_mixin(_mixin.subgraph):
    
    @hook_trigger('compile')
    def compile(self, 
                meta_node         : item.meta_node  , 
                exec_subgraph     : 'exec_subgraph' , 
                backwards_context : Backwards_Context = None,
                ):

        if backwards_context is None:
            backwards_context = Backwards_Context()

        # meta_node.pre_context_components()

        meta_node.compile(self, exec_subgraph, backwards_context)


#endregion



######## EXEC STRUCTURE ########
#region 


class exec_node_collection(_node_collection_base):
    ''' Merging done by operations on subgraph, Only exists to assert exec_nodes and call merge as required. '''
    @property
    def Bases(self)->dict[str,Any]:
        return self.context.root_graph.module_col.items_by_attr('_constr_bases_key_','node:exec')

    _coll_merge_on_setitem_ : bool = True
    _coll_mergeable_base_   : bool = True 
        #Should be contextual to allow for monadish?
        #May interfere with op to op, could rely on resulting behavior instead of rigid internal definition.

    def _coll_merge_handler_(self,left,right):
        #Assert same structural key, else throw error?
        left.merge(right)
        return left
    

class exec_subgraph(_subgraph_base):
    ''' Execution subgraph, changes base for exec_node_collection '''
    
    Nodes_Base = exec_node_collection
    
    memo : Memo

    @hook('__init__',mode='pre')
    def _init_hook_(self):
        self.memos = Memo()


class exec_subgraph_collection(_subgraph_collection_base):
    Base = exec_subgraph

#endregion 


######## TEST EXEC NODES ########
#region


class exec_test_int_socket(item.socket):
    ''' Hold, return '''
    Module        = None #SET THIS LATER 
    UID           = 'StringSocket'
    Version       = '1.0'
    Value_Type    = int
    Value_Default = _unset

class exec_test_add_node(item.exec_node):
    ''' Add two input sockets '''
    Module  = None #SET THIS LATER 
    UID     = 'TestExecNode'

    Version = '1.0'

    test_module_executed = False

    in_sockets   = [exec_test_int_socket,
                    exec_test_int_socket]
    out_sockets  = [exec_test_int_socket]

    @hook_trigger('execute')        #REQUIRED
    def execute(self)->None:
        i1 = self.in_sockets[0].execute()
        i2 = self.in_sockets[1].execute()
        val = i1 + i2
        self.out_sockets[0].value = val

#endregion


######## EXEC TESTS ########
#region


from ...models.base_node import graph, subgraph

def test_execute(graph:graph, subgraph:subgraph):
    with graph.Monadish_Env():
        new = exec_test_add_node.M(1,1) >> exec_test_add_node.M()
        head = subgraph.merge_walk_by_attr(new,)
    assert head != new
    subgraph.execute(head)
    assert 3 == head.out_sockets.sockets[0].exec_value

def test_struct_context(graph:graph, subgraph:subgraph):
    raise NotImplementedError('')

def test_value_context(graph:graph, subgraph:subgraph):
    raise NotImplementedError('')

def test_merge(graph:graph, subgraph:subgraph):
    raise NotImplementedError('')

def test_cache(graph:graph, subgraph:subgraph):
    raise NotImplementedError('')

_exec_test = module_test('Exec_Node_Tests',
    module      = None,
    funcs       = [
        test_execute,
    ],
    module_iten = { 'Distributed_Execution' : '1.0',
                    'Monadish':'1.2'}, 
    )

#endregion


######## MODULE DATA ########
#region


_loader_mixins_ = [
    exec_node_mixin
]

_loader_items_ = [
]

_new_structure_items_ = [
    exec_subgraph,
    exec_node_collection,
    exec_subgraph_collection,
]

_module_tests_ = [
    _exec_test
]

#endregion