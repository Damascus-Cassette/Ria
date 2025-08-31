

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
class socket_mixin():
    '''  A *lot* of boilerplate logic here '''
    
    Socket_Shape : socket_shape = socket_shape.MUTABLE

    @property
    def _Socket_Shape_Is_Single(self)->bool:
        return True

    @hook(event='__init__', mode = 'pre', see_args = False)
    def _init_(self):
        self._value = _socket_cache()
        self.current_context_state_key(self.address+'.state_key', default = _unset)
            #in an exec, short circuit and have single value. 

    @contextmanager
    def state_key_as(self,val):
        t = self.current_context_state_key.set(val)
        yield
        self.current_context_state_key.resset(t)

    @property
    def value(self):
        assert not (key:=self.current_context_state_key.get()) is _unset
        return self._value[key]
    
    @value.setter
    def value(self,value):
        assert not (key:=self.current_context_state_key.get()) is _unset
        self._value[key] = value


    @hook(event = 'execute', mode = 'wrap')
    def _execute_wrapper_(self,execute_func, exec_sg,backwards_context:dict,_return_state_token = False, *args, **kwargs)->tuple[Any,str]:
        # state_key = self.get_state_key(backwards_context)
        state_key = 'EXECUTE'

        direction = self.Direction

        with self.state_key_as(state_key):
            if (val:=self.value) is _unset:
                val =  execute_func(direction,*args,**kwargs)

                if not self.direction.upper() is 'OUT':
                    ... #TODO: Make store upstream value references
            if _return_state_token:
                return val, state_key
            return val
            #This ensures that the value can be accessed again outside of inline compile_call 

    @hook_trigger('execute')
    def execute(self,direction):
        ''' Router & Fallback function 
        Typical behavior reminder: in_sockets treat regular value as a default
        Incorperate declared fallback chain.
        TODO : Should also check source/type of socket eventuallly. 
        '''
        
        if direction.upper() != 'OUT':
            res =  self.execute_in_socket()
            if res is _unset:
                res = self.execute_in_fallback()
        else:
            res = self.execute_out_socket()
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
            
        for link in links:
            socket = link.other(self)
    
        TODO
            
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



    execute_in_fallback_chain  : tuple[str|_unset] = tuple()
    execute_out_fallback_chain : tuple[str|_unset] = tuple()
        #Fallback attributes to quiry/return if execute call upstream does not set a value on this socket
        #In all cases, execute should (even if the value is another _unset-like)
        #Keeping as it keeps inline with compile


    @hook(event = 'compile', mode = 'wrap')
    def _compile_wrapper_(self,compile_func, exec_sg,backwards_context:dict,_return_state_token = False, *args, **kwargs)->tuple[Any,str]:
        state_key = self.get_state_key(backwards_context)

        direction = self.Direction

        with self.state_key_as(state_key):
            if (val:=self.value) is _unset:
                val =  compile_func(direction,*args,**kwargs)

                if not self.direction.upper() is 'OUT':
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
            res =  self.compile_in_socket(*args,**kwargs)
            if res is _unset:
                res = self.compile_in_fallback(*args,**kwargs)
        else:
            res = self.compile_out_socket()
            if res is _unset:
                res = self.compile_out_fallback(*args,**kwargs)
        assert res is not _unset
        return res

    def compile_in(self,):
        ''' Returns values from upstream directly and does *not* cache on self atm.  '''
        links = self.links
        if  len(links) == 0:
            return _unset
            
        for link in links:
            socket = link.other(self)
        
        TODO
        

    def compile_out(self,):
        ''' call upstream execute which should store value on this socket in this socket's current context, 
        that set is auto caching '''
        self.context.node.execute() #This should always be blind to caller
        return self.value
    
    def compile_in_fallback(self,*args,**kwargs):
        ''' Compile returned None on Socket[In ] '''
        return self.generic_fallback(self.compile_in_fallback_chain,args,kwargs)

    def compile_out_fallback(self,*args,**kwargs):
        ''' Compile returned None on Socket[Out] '''
        return self.generic_fallback(self.compile_out_fallback_chain,args,kwargs)
        
    compile_in_fallback_chain  : tuple[str|Any] = tuple()
    compile_out_fallback_chain : tuple[str|Any] = tuple()
        #Fallback attributes or values to return if compile call upstream does not produce


    def generic_fallback(self,chain, args, kwargs):
        for attr in chain:

            if isinstance(attr,FunctionType):
                res = attr(*args,**kwargs)
            else:
                item = getattr(self,item)
                res = getattr(self,attr)
            
            if not (res is _unset):
                return res
            
        return _unset


class execute_node():
    ''' Statefull function container, socket.value is single context '''
    @hook_trigger('Execute')
    # @hook_trigger('Auto_Populate_Sockets', from_dict = True) #Could be usefull
    def execute(self,):
        ''' Execute using in_socket values via in_socket.execute()'''
        #Outputs should corrispond to sockets

    
class meta_node():

    @hook_trigger('Compile')
    # @hook_trigger('Auto_Populate_Sockets', from_dict = True) #Could be usefull
    def compile(self, exec_subgraph, backwards_context,): # structure_key, state_key, job, task): #Add to wrapper as Declarative fulllfillment
        ''' Execute using in_socket values via in_socket.compile()
        Cross-Nodes will have any inputs promised to a copy of self.Exec_Variant  
        ''' #Automatic construction?
        ...
    
class meta_subgraph():
    def compile(self,target, exec_subgraph, backwards_context=None):
        if backwards_context is None:
            backwards_context = Backwards_Context()
        target.compile(exec_subgraph,backwards_context)
