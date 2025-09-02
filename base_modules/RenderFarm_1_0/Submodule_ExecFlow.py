from .Data_Structures           import Backwards_Context
from ..Execution_Types          import item, _mixin, socket_shapes
from ..utils.print_debug        import debug_print_wrapper
from ...statics                 import _unset
from ...models.struct_hook_base import hook, hook_trigger,Hookable
from ...models.struct_module    import module_test
from ...models.base_node        import (subgraph            as _subgraph_base,
                                        node_collection     as _node_collection_base,
                                        subgraph_collection as _subgraph_collection_base,)


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
        raise NotImplementedError('')
        return True

    @hook(event='__init__', mode = 'pre', see_args=True,passthrough=False)
    def _init_(self, *args,**kwargs):
        self._value = _socket_cache()
        self.current_context_state_key = ContextVar(f'{hash(self)}.state_key', default = _unset)
            #Address is not garunteed to be known at this time 

    @contextmanager
    def state_key_as(self,val):
        t = self.current_context_state_key.set(val)
        yield
        self.current_context_state_key.reset(t)

    @property
    def value(self):
        assert not (key:=self.current_context_state_key.get()) is _unset
        return self._value[key]
    
    @value.setter
    def value(self,value):
        assert not (key:=self.current_context_state_key.get()) is _unset
        self._value[key] = value

    @property
    def exec_value(self):
        return self._value['EXECUTE']

    @hook(event = 'execute', mode = 'wrap')
    def _execute_wrapper_(self,execute_func)->tuple[Any,str]:
        # state_key = self.get_state_key(backwards_context)
        
        def wrapper(self,_return_state_token = False, *args, **kwargs):
            state_key = 'EXECUTE'

            direction = self.dir

            with self.state_key_as(state_key):
                if (val:=self.value) is _unset:
                    val =  execute_func(self, direction,*args,**kwargs)

                    if direction.upper() != 'OUT':
                        ... #TODO: Make store upstream value references
                if _return_state_token:
                    return val, state_key
                return val
                #This ensures that the value can be accessed again outside of inline compile_call 
        return wrapper

    @hook_trigger('execute')
    def execute(self,direction):
        ''' Router & Fallback function 
        Typical behavior reminder: in_sockets treat regular value as a default
        Incorperate declared fallback chain.
        TODO : Should also check source/type of socket eventuallly. 
        '''
        
        if direction.upper() != 'OUT':
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
            socket = link.other(self)
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


    @hook(event = 'compile', mode = 'wrap')
    def _compile_wrapper_(self,compile_func, exec_sg,backwards_context:dict,_return_state_token = False, *args, **kwargs)->tuple[Any,str]:
        state_key = self.get_state_key(backwards_context)

        direction = self.dir

        with self.state_key_as(state_key):
            if (val:=self.value) is _unset:
                val =  compile_func(direction,*args,**kwargs)

                if direction.upper() != 'OUT':
                    ... #TODO: Make store upstream value references
            if _return_state_token:
                return val, state_key
            return val
            #This ensures that the value can be accessed again outside of inline compile_call 

    @hook_trigger('compile')
    def compile(self,direction,*args,**kwargs):
        ''' Router & Fallback function 
        Typical behavior reminder: in_sockets treat regular value as a default
        Incorperate declared fallback chain.
        TODO : Should also check source/type of socket eventuallly. 
        '''
        
        if direction.upper() != 'OUT':
            res =  self.compile_in(*args,**kwargs)
            if res is _unset:
                res = self.compile_in_fallback(*args,**kwargs)
            if self._Socket_Shape_Is_Single():
                for x in res: assert x is not _unset
        else:
            res = self.compile_out()
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
            socket = link.other(self)
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
    def address(self)->str:
        c = self.context
        return '.'.join([c.root_graph.key , c.subgraph , self.key])

    @hook_trigger('Compile')
    # @hook_trigger('Auto_Populate_Sockets', from_dict = True) #Could be usefull
    def compile(self, exec_subgraph, backwards_context,): # structure_key, state_key, job, task): #Add to wrapper as Declarative fulllfillment
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
        return target.execute()
        #Task Discovery Error handling, Diff & upload to manager in another module

    @hook_trigger('compile')
    @debug_print_wrapper(0)
    def compile(self,target, exec_subgraph, backwards_context=None):
        if backwards_context is None:
            backwards_context = Backwards_Context()
        target.compile(exec_subgraph,backwards_context)
        #Task Discovery Error handling, Diff & upload to manager in another module

_exec_flow_mixins_ = [
    socket_mixin,
    execute_node_mixin,
    meta_node_mixin,
    subgraph_mixin,
]

_exec_flow_items_ = [

]

#### TESTS ####

from .Test_Items import (exec_test_int_socket, 
                         exec_test_add_node  )

@debug_print_wrapper(0)
def test_execute(graph,subgraph):
    with subgraph.As_Env(auto_add_nodes = True, auto_add_links = True):
        # header = exec_test_add_node.M(1,1) >> exec_test_add_node.M(1,1) 
        a = exec_test_add_node.M(1,1)
        b = exec_test_add_node.M(1,1)
        a.out_sockets[0].links.new(b.in_sockets[0])
    subgraph.execute(b.out_sockets[0])
    print ('RES VALUE:',b.out_sockets[0].exec_value)
    assert a.out_sockets[0].exec_value == 2
    assert b.out_sockets[0].exec_value == 3

_execflow_test_ = module_test('Exec_Node_Tests',
    module      = None,
    funcs       = [
        test_execute,

    ],
    module_iten = { 
        'Distributed_Execution' : '1.0',
        'Monadish_Interface'    : '1.2'}, 
    )