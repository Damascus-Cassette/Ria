
class _empty():
    ''' Utility None '''

class common_root:
    ''' Utility Root '''

class s_input():
    Context : Any
    def __init__(self, as_type, uuid=None, in_context:str|None=None, default=None, default_args=None, default_kwargs=None):
        self.as_type        = type    
        self.uuid           = uuid
        self.in_context     = in_context
        self.default        = default
        self.default_args   = default_args   if default_args   else []
        self.default_kwargs = default_kwargs if default_kwargs else {}
    
    def set_value(self,data):
        self.data = data
    
    def set_default(self,as_type=None):
        if not as_type:
            as_type = self.type

        if self.default:
            self.data = as_type(self.default)
        else:
            self.data = as_type(*self.default_args,**self.default_kwargs)

    def set_context_insertion(self):
        if self.in_context:
            setattr(self.Context,self.in_context,self)
    
    def return_chain_id(self,data:dict,chain,self_key):
        data[chain+'.'+self_key] = self
    
    def get(self):
        if issubclass(self.data.__class__,common_root):
            return self.data.get()
        return self.data

class formatted_var():
    
    def __init__(data):
        ...

    def get(self):
        ...
    

class loader_context():
    context   = ContextVar('context' , default = None)
    uuid_dict = ContextVar('uuid_d'  , default = None)
    chain_dict= ContextVar('chain_d' , default = None)

@ContextManager
def settings_loader(context,uuid_dict,chain_dict):
    try:
        token1 = loader_context.context.set(context)
        token2 = loader_context.uuid_dict.set(uuid_dict)
        token3 = loader_context.chain_dict.set(chain_dict)
        yield
    except:
        raise
    finally:
        loader_context.context.reset(token1)
        loader_context.uuid_dict.reset(token2)
        loader_context.chain_dict.reset(token3)

class settings_root(common_root):
    ''' Recursive instance of settigns item. Each input required to be s_input instance '''
    ''' Next version may be best as a class factory '''

    @property
    def Context(self):
        return self._Context.get()

    _uuids = {}

    def __init__(self,data,Context=None):
        self.context = loader_context.context.get()

    def set_value(self,data):
        for k,v in data.keys():
            value_container = getattr(self,k)
            assert issubclass(value_container,common_root)
            value_container.set_value()
            value_container.Context = self.Context
        
    def set_context():
        ...
