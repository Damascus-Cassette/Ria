from .Env_Variables             import Backwards_Context
from ..Execution_Types          import item, _mixin, socket_shapes
from ..utils.print_debug        import debug_print_wrapper
from ...statics                 import _unset
from ...models.struct_hook_base import hook, hook_trigger,Hookable
from ...models.struct_module    import module_test
from .backwards_context         import BackwardsContextType
from .Submodule_Cache import Cache
from .Env_Variables   import CACHE

from contextvars import ContextVar
from contextlib  import contextmanager
from typing      import Any, Self
from types       import FunctionType
from enum        import Enum

class _socket_cache(dict):
    def __missing__(self, key):
        ''' Key should always be unique globally, or if not it still collides due to the context/state key 
        May have to make generic typed collection I think?
        '''
        self[key] = _unset
        return _unset

class socket_shape(Enum):
    MUTABLE  = 'MUTABLE'

    SINGLE   = 'SINGLE'
    MULTIPLE = 'MULTIPLE'
    # DICT     = 'DICT'
        #Returns node -> value. A post process?


# active_context = ContextVar('active_context', default = '')
class socket_mixin(_mixin.socket):
    '''  A *lot* of boilerplate logic here '''
    
    Socket_Shape : socket_shape = socket_shape.MUTABLE

    @property
    def address(self)->str:
        c = self.context
        return '.'.join((c.node.address, self.dir, self.label)) 

    @property
    def _Socket_Shape_Is_Single(self)->bool:
        return True
        raise NotImplementedError('')
        return True

    @hook(event='__init__', mode = 'pre', see_args=True,passthrough=False)
    def _init_(self, *args,**kwargs):
        self._value = _socket_cache()
        # self.current_context_state_key = ContextVar(f'{hash(self)}.state_key', default = _unset)

    # @contextmanager
    # def state_key_as(self,val):
    #     t = self.current_context_state_key.set(val)
    #     yield
    #     self.current_context_state_key.reset(t)

    @property
    def value(self):
        # if not (key:=getattr(self,'override_value_state_key',None)):
        #     assert not (key:=self.state_key) is _unset
        key = self.value_key
        return self._value[key]
    
    @value.setter
    def value(self,value):
        
        # if not (key:=getattr(self,'override_value_state_key',None)):
        #     key = self.value_key

        key = self.value_key
        self._value[key] = value

    @property
    def exec_value(self):
        return self._value['EXECUTE']
    
    @property
    def value_key(self):
        return self.context.node.value_key
        

    # @hook(event = 'execute', mode = 'wrap')
    # def _execute_wrapper_(self,execute_func)->tuple[Any,str]:
        
    #     def wrapper(self,_return_state_token = False, *args, **kwargs):

    #         direction = self.dir

    #         if (val:=self.value) is _unset:
    #             val =  execute_func(self, direction,*args,**kwargs)

    #             if direction.upper() != 'OUT':
    #                 ... #TODO: Make store upstream value references

    #         if _return_state_token:
    #             return val, state_key
    #         return val
    #             #This ensures that the value can be accessed again outside of inline compile_call 
    #     return wrapper

    @hook_trigger('execute')
    def execute(self):
        ''' Router & Fallback function 
        Typical behavior reminder: in_sockets treat regular value as a default
        Incorperate declared fallback chain.
        TODO : Should also check source/type of socket eventuallly. 
        '''
        
        if self.dir.upper() != 'OUT':
            res =  self.execute_in()
            if res is _unset:
                res = self.execute_in_fallback()
        else:
            res = self.execute_out()
            if res is _unset:
                res = self.execute_out_fallback()
        if res is _unset:
            raise Exception(f'Unset socket value during execution : {self.address}')
        return res

    def execute_in(self,):
        ''' Returns values from upstream directly and does *not* cache on self atm.  '''
        links = self.links
        if  len(links) == 0:
            return _unset

        res = []            
        for link in links:
            socket = link.out_socket
            assert socket is not self
            res.append(socket.execute())
        
        if self._Socket_Shape_Is_Single:
            return res[0]
        return res
    
            
    def execute_out(self,):
        ''' call upstream execute which should store value on this socket in this socket's current context, 
        that set is auto caching '''
        self.context.node.execute() #This should always be blind to caller
        return self.value

    def execute_in_fallback(self,*args,**kwargs):
        ''' Execute returned None on Socket[In ] '''
        return self.generic_fallback(self.execute_in_fallback_chain,args,kwargs)

    def execute_out_fallback(self,*args,**kwargs):
        ''' Execute returned None on Socket[Out]'''
        return self.generic_fallback(self.execute_in_fallback_chain,args,kwargs)



    execute_in_fallback_chain  : tuple[str|_unset] = ('Default_Value',)
    execute_out_fallback_chain : tuple[str|_unset] = ('Default_Value',)
        #Fallback attributes to quiry/return if execute call upstream does not set a value on this socket
        #In all cases, execute should (even if the value is another _unset-like)
        #Keeping as it keeps inline with compile


    # @hook(event = 'compile', mode = 'wrap',see_args=True)
    # def _compile_wrapper_(self,compile_func, exec_sg, backwards_context:dict, _return_state_token = False, *args, **kwargs)->tuple[Any,str]:

    #     state_key = self.get_state_key(backwards_context)
    #     direction = self.dir

    #     def wrapper(self,*args,**kwargs):
    #         with self.state_key_as(state_key):
    #             if (val:=self.value) is _unset:
                    
    #                 val =  compile_func(self,direction,*args,**kwargs)

    #                 if direction.upper() != 'OUT':
    #                     ... #TODO: Make store upstream value references
    #             if _return_state_token:
    #                 return val, state_key
    #             return val
    #             #This ensures that the value can be accessed again outside of inline compile_call 
    #     return wrapper

    @hook_trigger('compile')
    def compile(self,*args,**kwargs):
        ''' Router & Fallback function 
        Typical behavior reminder: in_sockets treat regular value as a default
        Incorperate declared fallback chain.
        TODO : Should also check source/type of socket eventuallly. 
        '''
        
        if self.dir.upper() != 'OUT':
            res =  self.compile_in(*args,**kwargs)
            if res is _unset:
                res = self.compile_in_fallback(*args,**kwargs)
            if not self._Socket_Shape_Is_Single:
                for x in res: assert x is not _unset
        else:
            res = self.compile_out(*args,**kwargs)
            if res is _unset:
                res = self.compile_out_fallback(*args,**kwargs)
        assert res is not _unset
        return res

    def compile_in(self,*args,**kwargs):
        ''' Returns values from upstream directly and does *not* cache on self atm.  '''
        links = self.links
        if  len(links) == 0:
            return _unset

        res = []            
        for link in links:
            socket = link.out_socket
            res.append(socket.compile(*args,**kwargs))
        
        if self._Socket_Shape_Is_Single:
            return res[0]
        return res

    def compile_out(self,*args,**kwargs):
        ''' call upstream execute which should store value on this socket in this socket's current context, 
        that set is auto caching '''
        self.context.node.compile(*args,**kwargs) #This should always be blind to caller
        return self.value
    
    def compile_in_fallback(self,*args,**kwargs):
        ''' Compile returned None on Socket[In ] '''
        return self.generic_fallback(self.compile_in_fallback_chain,args,kwargs)

    def compile_out_fallback(self,*args,**kwargs):
        ''' Compile returned None on Socket[Out] '''
        return self.generic_fallback(self.compile_out_fallback_chain,args,kwargs)
        
    compile_in_fallback_chain  : tuple[str|Any] = ('Default_Value',)
    compile_out_fallback_chain : tuple[str|Any] = ('Default_Value',)
        #Fallback attributes or values to return if compile call upstream does not produce


    def generic_fallback(self,chain, args, kwargs):
        for attr in chain:

            if isinstance(attr,FunctionType):
                res = attr(*args,**kwargs)
            else:
                # item = getattr(self,attr)
                res = getattr(self ,attr)
            
            if not (res is _unset):
                return res
            
        return _unset


class execute_node_mixin(_mixin.exec_node):
    ''' Statefull function container, socket.value is single context '''

    @property
    def value_key(self):
        return 'EXECUTE' 

    @hook_trigger('Execute')
    # @hook_trigger('Auto_Populate_Sockets', from_dict = True) #Could be usefull
    def execute(self,):
        ''' Execute using in_socket values via in_socket.execute()'''
        #Outputs should corrispond to sockets

    @property
    def address(self)->str:
        c = self.context
        return '.'.join([c.root_graph.key , 'EXEC' , self.key])

    
class meta_node_mixin(_mixin.meta_node):
    ''' Stateful function container that 'compiles' to am exec graph '''


    @property
    def value_key(self):
        return self.state_key

    @property
    def address(self)->str:
        c = self.context
        return '.'.join([c.root_graph.key , c.subgraph.label , self.key])

    @hook(event='__init__', mode = 'pre', see_args=True,passthrough=False)
    def _init_(self, *args,**kwargs):
        self._value = _socket_cache()
        self.current_context_state_key = ContextVar(f'{hash(self)}.state_key', default = _unset)
            #Address is not garunteed to be known at this time 

    @hook_trigger('compile')
    # @hook_trigger('Auto_Populate_Sockets', from_dict = True) #Could be usefull
    def compile(self, exec_subgraph): # structure_key, state_key, job, task): #Add to wrapper as Declarative fulllfillment
        ''' Execute using in_socket values via in_socket.compile()
        Cross-Nodes will have any inputs promised to a copy of self.Exec_Variant  
        ''' #Automatic construction?
    

class subgraph_mixin(_mixin.subgraph):
    ''' Add flow '''

    @hook_trigger('execute')
    @debug_print_wrapper(0)
    def execute(self, target, backwards_context=None):
        # if backwards_context is None:
        #     backwards_context = Backwards_Context()
        if backwards_context is None:
            backwards_context = BackwardsContextType()
        t = Backwards_Context.set(backwards_context)
        target.init_state_components()
        res =  target.execute()
        Backwards_Context.reset(t)
        return res
        #Task Discovery Error handling, Diff & upload to manager in another module

    @hook_trigger('compile')
    @debug_print_wrapper(0)
    def compile(self,target, exec_subgraph, backwards_context=None):
        if backwards_context is None:
            backwards_context = BackwardsContextType()
        t = Backwards_Context.set(backwards_context)
        target.init_state_components()
        res = target.compile(exec_subgraph,)
        Backwards_Context.reset(t)
        return res
        #Task Discovery Error handling, Diff & upload to manager in another module




#### TESTS ####

from .Test_Items import (exec_test_int_socket , 
                         exec_test_add_node   ,
                         meta_test_socket     ,
                         meta_test_add_node   )


@debug_print_wrapper(0)
def test_execute(graph,subgraph):
    CACHE.set(Cache())
    with subgraph.As_Env(auto_add_nodes = True, auto_add_links = True):
        # header = exec_test_add_node.M(1,1) >> exec_test_add_node.M(1,1) 
        a = exec_test_add_node.M(1,1)
        b = exec_test_add_node.M(1,1)
        new_link = a.out_sockets[0].links.new(b.in_sockets[0])
    assert new_link.out_socket is a.out_sockets[0]

    CACHE.set(Cache())
    subgraph.execute(b.out_sockets[0])
    print(a.out_sockets[0]._value)

    assert a.out_sockets[0].exec_value == 2
    assert b.out_sockets[0].exec_value == 3

def test_compile(graph,subgraph):
    CACHE.set(Cache())
    with subgraph.As_Env(auto_add_nodes = True, auto_add_links = True):
        a = meta_test_add_node.M(1,1)
        b = meta_test_add_node.M(a.out_sockets[0],1) 

        # b = meta_test_add_node.M(1,1) 
        # new_link = a.out_sockets[0].links.new(b.in_sockets[0])

    print(*a.in_sockets)
    print(*b.in_sockets)

    # print ('META NODES:',*(subgraph.nodes.values()))
    # print ('META LINKS:',*(subgraph.links.values()))
    # for x in subgraph.links:
        # print(' LINK: ', x.key, hash(x))
        # print('     OUT', x.out_socket.context.Repr())
        # print('     IN ', x.in_socket.context.Repr())
    assert len(subgraph.nodes) == 2
    assert len(subgraph.links) == 1

    #Atm with this particular node's logic, it should always produce a exec_node.
    #Future cases are to allow the compile to result in a value instead of an promise (execution-node) in certain use cases

    exec_graph = graph.subgraphs.new(f'{subgraph.key}.EXECUTE')
    res_node = subgraph.compile(b,exec_graph)

    # print('nodes:',*(exec_graph.nodes.values()))
    # print('links:',*(exec_graph.links.values()))
    
    assert len(list(exec_graph.nodes.values())) == 2
    assert len(list(exec_graph.links.values())) == 1
    
    assert exec_graph.execute(res_node.out_sockets[0]) == 3

def test_cache_disc(graph,subgraph):
    CACHE.set(Cache())
    with subgraph.As_Env(auto_add_nodes = True, auto_add_links = True):
        ...
        # a = meta_test_add_node.M(1,1)
        # b = meta_test_add_node.M(a.out_sockets[0],1) 
        # ...
    

    
_exec_flow_mixins_ = [
    socket_mixin,
    execute_node_mixin,
    meta_node_mixin,
    subgraph_mixin,
]

_exec_flow_items_ = [

]

_exec_flow_tests_ = [        
    module_test('Exec_Node_Tests',
        module      = None,
        funcs       = [
            test_execute,
            test_compile,
            test_cache_disc,
        ],
        module_iten = { 
            'Distributed_Execution' : '1.0',
            'Monadish_Interface'    : '1.2'}, 
        )
]