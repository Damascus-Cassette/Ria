from ...models.struct_module    import module, module_test
from ...models.base_node        import socket_group, node_set_base
from ..Execution_Types          import _mixin, item
from ...models.struct_hook_base import hook, hook_trigger,_unset
from ..utils.print_debug import (debug_print_wrapper as dp_wrap, 
                                 _debug_print        as dprint ,
                                 debug_level                   , 
                                 debug_targets                 )

from types  import FunctionType
from typing import Any

class main(module):
    ''' Execution engine re-write for shared items between distributed & local use 
    This adds 
        - Node execution modes:
            - Compile
            - Compile Placeholders (Callback for execute)
            - Execution
        - Tasks
            - Nodes that declare them 
            - Deps
            - Abstract repr
        - Memo
            - For true random output and externally declared values
        - User inputs
        - Checkpoints & Breakpoints
            - Branching and diffing
    '''
    UID     = 'Distributed_Execution_Common'
    Version = '1.0'
    Dependencies = [
        ('Monadish','=1.2')
    ]

######## ERRORS ########
# region

class ContextMissing(Exception):
    '''Forward resolution of keys was not consumed properly by a zone end, or otherwise context for context was not met. If unconstrained forward context is OK, have default be declared as a different unset flag.'''

#endregion

######## UNIQUE CLASSES ########
#region

from contextvars import ContextVar
from contextlib  import contextmanager


class Backwards_Context(dict):    
    ''' May convert to a collection to allow better export & typed import via regular fileio '''

    def _export_(self,)->dict:
        # Export current key values w/a (not _unset) 
        #  & call basemodel export & import on them w/a (must be typed context??)
        ... 

    def __init__(self):
        super().__init__()
        self['_chain'] = tuple()

    def __missing__(self,k):
        self[k] = r = ContextVar('k', default = _unset)

    def set(self,key_or_values:dict|str, value:Any = _unset)->dict|Any:
        if isinstance(key_or_values,str):
            assert not (value is _unset)
            return res[key_or_values].set(value)

        res = {}
        for k,v in key_or_values.items():
            res[k] = self[k].set(v)

        return res
    
    def get(self, keys:dict|tuple|str)->dict|tuple|Any:
        if isinstance(keys,str):
            return self[keys].get()
        elif isinstance(keys,dict):
            res = {}
            for k,v in keys.items():
                res[k] = self[k].get()
        else:
            res = []
            for k in keys:
                res.append(self[k].get())
            return tuple(res)

    def reset(self,tokens:dict):
        for k,t in tokens.items():
            self[k].reset(t)

    @contextmanager
    def checkin(self, ident):
        t = self.set('_chain', self.get('_chain') + (ident,))
        yield
        self.reset()

    @contextmanager
    def values_as(self,values:dict):
        ret = {}
        for k, v in values.items():
            ret[k] = self[k].set(v)
        yield
        for k, t in ret.items():
            self[k].reset(t)


class Memo_Item(Item, BaseModel,ConstrBase, Hookable):
    ...

class Memo(Item, BaseModel, typed_collection_base, ConstrBase, Hookable):
    ''' Custom collection of floating uids for replaceing values by address on exec OR meta at execution time. ( Meta replaces all values, just flat )
    Values must be typed & grouped somehow ...

    ie f'exec/{meta_graph}.{node}.{uid}.{attr}'                -> value
    ie f'exec/{meta_graph}.{node}.{uid}.{dir}.{socket}.{attr}' -> value
    '''

class Memo_Collection(BaseModel, typed_collection_base, ConstrBase, Hookable):
    ''' Structure for manager, probably  '''
    ...


class Task_Base(Item, BaseModel):
    dependencies : Self

class Task_Graph(Task_Base):
    ''' Discovered Split on groupings of executions in the graph or other
     Should have allowences for reporting back on the task and the like '''

class Task_Generic(Task_Base):
    ''' Generic Distributed Task '''


class Task_Collection(BaseModel, typed_collection_base):
    _Bases = [Task_Graph, Task_Generic]


class Job(Item, BaseModel):
    ''' Series of individual tasks ascociated with a graph or otherwise. '''


class Job_Collection(BaseModel, collection_base):
    _Base = Job


class utils():
    @staticmethod
    def is_promise(item)->bool:
        return issubclass(item.context.subgraph.__class__, exec_subgraph)

from ...models.base_node import (node_collection     as _node_collection_base,
                                 subgraph            as _subgraph_base, 
                                 subgraph_collection as _subgraph_collection_base)

#DEFER: compose instead of inherit when base stabalizes a bit more!

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


######## MIXINS ########
# region

class graph_mixin(_mixin.graph):
    ''' Contain job datastructure & session context/allowences '''
    jobs           : None
    tasks          : None
    exec_subgraphs : exec_subgraph_collection

    @hook('__init__',mode='pre')
    def _init_hook_(self):
        self.exec_subgraphs = exec_subgraph_collection()


class socket_mixin(_mixin.socket):

    Deterministic      : bool|None = None
    Mem_Cachable       : bool|None = None
    Disc_Cachable      : bool|None = None
    Cache_Check_Server : bool|None = None


class meta_node_mixin(_mixin.meta_node):
    '''  '''

    Deterministic      : bool
    Mem_Cachable       : bool
    Disc_Cachable      : bool

    Cache_Check_Server : bool


    uuid : str|FunctionType
        # UUID for this node, cross-graph & global.
        # Maybe just (Graph.name + Subgraph.name + Node.name)

    #cache keys
    backwards_context_deps : tuple[str] = tuple()
        #Pre-walk-sum contextual keys
        #Consider also allowing lambda's for flexability

    # cache_value_key       : str
    cache_structural_key  : str
        #State of node structure leading to this node
    cache_contextual_keys :tuple[str]
        #post-walk-sum contextual keys
        #Abstract two above to contextVars that the graph can reset, or dependant otherwise graph dependant values

    def value_key(self)->str:
        ''' Local state of node apart from sockets.
        Use minimally in meta-nodes. Must always be defined in sockets'''
        return ''
    
    def generate_context_components(self)->tuple[str, tuple[str]]:
        ''' Walks tree and returns 
        - structural_key from uidsum(value & structural_key)
        - backwards dependency keys
        This implimentation is socket order-dependant, 
            sum and similar nodes would not have to be (sort inputs to prevent)
        '''
        
        #Requires local-cache dependant on context.graph value to optimize

        deps = tuple()
        key  = self.value_key() 

        for socket in (*self.in_sockets.sockets, *self.out_sockets.sockets):
            _key, _deps = socket.generate_context_components()
            key =+ _key
            deps =+ _deps
        
        deps = sorted(list(set[deps]))
            #Dep keys must be deduped and sorted pre-evaluation have proper result.

        return uuid.sum(key), deps
    
    def context_state(self, structural_key, contextual_keys, backwards_context:Backwards_Context):
        ''' Resolve structural_key, contextual_deps and backwards_context to forward hash to check cache for value'''
        k = tuple

        for attr in contextual_keys:
            if backwards_context[attr] is _unset:
                raise ContextMissing(self,attr,backwards_context)
            k =+ tuple(uuid.from_value(backwards_context[attr]))

        k =+ (structural_key,)

        return uuid.sum(k) 
    
    @hook(event='compile', mode='pre', key='_ensure_context_state_', passthrough=True)
    def _ensure_context_state_(self, exec_graph, backwards_context:Backwards_Context)->Any|_unset:
        ''' Add context_state to arguments '''
        if (self.cache_contextual_keys.get() is _unset) or (self.cache_structural_key.get() is _unset):
            struct_key, context_keys = self.generate_context_components
            self.cache_structural_key .set(struct_key)
            self.cache_contextual_keys.set(context_keys)
        
        return exec_graph, backwards_context, self.context_state(self.cache_structural_key, self.cache_contextual_keys, backwards_context)

    @hook(event='compile', mode='context', key='compile_enter_context', see_args=True)
    def _ensure_context_state_(self, exec_graph, backwards_context:Backwards_Context, context_state)->Any|_unset:
        ''' Set context in backwards_context item '''
        with backwards_context.checkin(self):
            t =  backwards_context.context.set(context_state)
            yield
            backwards_context.context.reset(t)

    @hook_trigger('compile') #Takes care of caching, state mgmt
    def compile(self, exec_graph, backwards_context, context_state):
        raise NotImplementedError(f'Compile not implimented in node {self.UID}!')
    
    @hook_trigger('compile') #Takes care of caching, state mgmt
    def _compile_example__shared_(self, exec_graph, backwards_context:Backwards_Context, context_state):
        ''' For when a node can both execute or return a promise, based on input values 
        Node shape is sum(in_[n]) -> out_1
        Node is assumed to have an equivilent exec node stored in self.Exec_Variant
            - Based on current structure, this is required to be a different class (as exec and meta nodes have different bases)
        '''

        execute_in_compile = True
        vals = []
        for socket in (*self.in_sockets.sockets, *self.out_sockets.sockets):
            val = socket.compile(exec_graph, backwards_context)
                #sets compile_value in context and returns.
            if utils.is_promise(val): # meaning val.context.subgraph is an exec_graph, or node is an exec node
                execute_in_compile = False
            vals.append(val)
        
        if execute_in_compile:
            res = self.execute_in_compile(vals)
            self.out_sockets.sockets[0].compile_value = context_state
        
        else:
            with exec_graph.Monadish_Env(key = context_state):
                vals >> (res_node:=self.Exec_Variant(default_sockets = True))

            self.out_sockets.sockets[0].compile_value = res_node.out_sockets.sockets[0]

    @hook_trigger('compile') #Takes care of caching, state mgmt
    def _compile_example__multi_zone_end_(self, exec_graph, backwards_context, context_state):
        ''' For a multi-zone, called on the end node,
        Local resulting node is assumed to have shape of (in_[n] -> out_[n]:list)
        '''
        start_node = self.node_set['start']
        start_node.compile_upstream(exec_graph, backwards_context)
        
        if start_node.check_require_placeholder():
            placeholder = compile_placeholder.create(callbacks = ((self,'compile'),) , backwards_context = backwards_context, context_state = context_state )
            for p_socket, s_socket in zip(placeholder.out_sockets.sockets, self.out_sockets.sockets):
                s_socket.compile_value = p_socket
            exec_graph[context_state] = placeholder
            return
        
        with exec_graph.graph.Monadish_Env(key = context_state, merge_attr = 'cache_structural_key', auto_merge_target = exec_graph):
            for i in range(start_node.sockets['range'].compile_value):
                res=self.Exec_Variant()
                with backwards_context.set({self.uuid : i}):
                    for x in self.in_sockets.sockets:
                        x.compile(exec_graph,backwards_context) >> ~res
            exec_graph.merge_in(res)

        for r_socket, s_socket in zip(res.out_sockets.sockets, self.out_sockets.sockets):
            s_socket.compile_value = r_socket
        
        return
        
    @hook_trigger('compile') #Takes care of caching, state mgmt
    def _compile_example__repeat_zone_end_(self, exec_graph, backwards_context, context_state):
        ''' For a repeat zone, as each step forward can become a placeholder this can be somewhat complicated. 
        1. step initial is or is not a placeholder.
        if so:
            2a. Make placeholder call self with context(start)
        if not:
            2a. call start node to compile for each (repeat_index - 1) 
                - Output of previous step becomes input of current
                - if not placeholder, call from back to compile upstream (left)
                - Create start-end nodes for each anyway (as just a passthrough)
            3b. After last iteration, compile locally the last time

            Context here for the values placed on sockets may have to be overridden to fetch local results correctly? 
            Or other way of matching context of start to context of end when hit during compilation.
        ''' #I think that makes some sort of sense at least...

        start_node = self.node_set['start']
        start_node.compile_upstream(exec_graph, backwards_context)

        if start_node.check_require_placeholder():
            placeholder = compile_placeholder.create(callbacks = ((self,'compile'),) , exec_graph = exec_graph, backwards_context = backwards_context, context_state = context_state )
            for p_socket, s_socket in zip(placeholder.out_sockets.sockets, self.out_sockets.sockets):
                s_socket.compile_value = p_socket
            exec_graph[context_state] = placeholder
            return

        repeat_range = start_node.sockets['repeat'].compile_value
        with exec_graph.Monadish_Env(key = context_state):
            for i in range(repeat_range - 1):
                with backwards_context.set({self.uuid : i+1}):
                    new_head = start_node.compile(exec_graph, backwards_context)
            
            with backwards_context.set({self.uuid : repeat_range}):
                vals = []
                for socket in (*self.in_sockets.sockets, *self.out_sockets.sockets):
                    val = socket.compile(exec_graph, backwards_context)
                    vals.append(val)
                res = self.Exec_Variant()
                vals >> ~res
                
        for r_socket, s_socket in zip(res.out_sockets.sockets, self.out_sockets.sockets):
            s_socket.compile_value = r_socket

        #Not making a lot of sense here. Prob needs to be a two-parter to find teh starting node's last compile value or similar. 
        # End call start to compile with repeat_index -1, which loops back to head, Then compile last from current endpoint.

        #Another thought: if the head calls back and de-incriments by one and calls the end again every resulting solution should be convergent and the cache should catche doubles.. Right?
        #No way to know. Focus on short term solutions


class exec_node_mixin(_mixin.exec_node):
    ''' A atomic unit of work node with a contextual ID in a graph that merges based on that context ID '''
 
    Deterministic      : bool
    Mem_Cachable       : bool
    Disc_Cachable      : bool

    Cache_Check_Server : bool

    UUID_Sources : list[str] 
        #Sources for this node, deduplicated by context key walk

    # cache_id_context : str #Upstream-Node context hash
    # cache_id_value   : str #Incoming socket - value hash

    cache_value_key      : str
    cache_structural_key : str
    # cache_memo_keys, Similar to cache_contextual_keys: all upstream items by UID to check against memo to hash as well
    # cache_contextual_keys as memo key default unset?


    @hook_trigger('execute')
    def execute():
        ...

    @hook(event='execute', mode='cache', key='_compile_cache_')
    def _execute_cache_(self,*args,**kwargs)->Any|_unset:
        ''' Check cache w/a and h/a here '''
        return _unset


main._loader_mixins_ = [
    graph_mixin     ,
    meta_node_mixin ,
    exec_node_mixin ,
    socket_mixin    ,
    exec_node_mixin ,
]

#endregion


######## BUILT IN NODES ######## 

class compile_placeholder(item.exec_node):
    ''' Placeholder in execution, to re-trigger compile with a stored context toward a specific node 
    This allows defering compilation that depends on un-executed variables.
    '''

    UID = 'EXEC_compile_placeholder'
    Version = '1.0'

    in_sockets  = []
    out_sockets = []

    target_node     : item.meta_node
    cached_context  : dict|BaseModel
        # Potential problem: Storing reference across graphs. 
        # May have to hack it and store the graph & node ID.

    def execute(self, context, subgraph):
        ''' Call target node to compile '''
        ...

    @classmethod
    def create(cls,node)->Self:
        ''' Format toward the incoming node and store a copy of the context locally
        Should be 1 to 1 with the incoming node's sockets.
        ''' #Consider using copy and _context_walk_ manually to graft onto this object?
        ... 


######## TEST NODES ########
# region

class node_exec_example(item.exec_node):
    UID     = 'EXEC_add'
    Version = '1.0'

    in_sockets  = []
    out_sockets = []

    # @hook_trigger('execute') #Should be Auto Wrapped
    def execute(self, context, subgraph, session):
        ...

class node_meta_example(item.meta_node):
    UID     = 'META_add'
    Version = '1.0'
    
    in_sockets  = []
    out_sockets = []
    
    # @hook_trigger('compile') #Should be Auto Wrapped
    def compile(self, context, subgraph):
        ...


class repeat_zone_meta(node_set_base):
    ''' Node set that compiles'''

    class zone_start(item.meta_node):
        UID = 'META_repeat_zone_start'
        Version = '1.0'

        in_sockets  = []
        out_sockets = []

        def compile(self, context, subgraph):
            ...

    class zone_end(item.meta_node):
        UID = 'META_repeat_zone_end'
        Version = '1.0'

        in_sockets  = []
        out_sockets = []

        def compile(self, context, subgraph):
            ...
        
class multi_zone_meta(node_set_base):
    ''' Threading compilation'''

    class zone_start(item.meta_node):
        UID = 'META_multi_zone_start'
        Version = '1.0'

        in_sockets  = []
        out_sockets = []

        def compile(self, context, subgraph):
            ...

    class zone_end(item.meta_node):
        UID = 'META_multi_zone_end'
        Version = '1.0'

        in_sockets  = []
        out_sockets = []

        def compile(self, context, subgraph):
            ...

main._loader_items_ = [
    node_exec_example,
    node_meta_example,
    *repeat_zone_meta.Nodes_Types,
    *multi_zone_meta.Nodes_Types,
]

#endregion



######## TESTS ########
#region

def test_exec(graph, subgraph):
    exec_graph = graph.exec_subgraphs.new(name = f'{subgraph}_exec_test')
    
    

def test_compile(graph,subgraph):
    with graph.Monadish_Env(auto_join_target = subgraph) as _sg:
        (n1:=node_meta_example.M()) >> (n2:=node_meta_example.M())
    exec_graph = graph.exec_subgraphs.new()
    subgraph.compile(exec_graph, n2, context = None)
    res = exec_graph.execute(n2.find_children(exec_graph)[0])
    assert res == 3

def test_zone_repeat_compile(graph,subgraph):
    ...

def test_zone_multi_compile(graph,subgraph):
    ...

def test_placeholder_creation(graph,subgraph):
    ...

def test_placeholder_execution(graph,subgraph):
    ...

# def test_task_discovery():
#     ...
# def test_task_depedency():
#     ...
# def test_task_():
#     ...

main._module_tests_.append(
    module_test('TestA',
        module      = main,
        funcs       = [
            test_exec,
            test_compile,
            test_zone_repeat_compile,
            test_zone_multi_compile,
            test_placeholder_creation,
            test_placeholder_execution,
        ],
        module_iten = {main.UID : main.Version,
                      'Monadish':'1.2'}, 
        ))


#endregion