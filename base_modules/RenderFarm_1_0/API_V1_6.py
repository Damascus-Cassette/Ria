
from functools import partial, wraps
from enum      import Enum
from inspect   import isclass
class PRIMARY():...
class _UNSET():...

class _method():
    ''' Local inst-method cls '''
    def __get__(self, inst, inst_cls):
        if inst is None:
            return self
        else:
            return partial(self,inst)

    def __init__(self, func):
        self.func = func
    
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

class Command(Enum):
    GET    = 'GET'
    POST   = 'POST'
    PATCH  = 'PATCH'
    DELETE = 'DELETE'

class Entity_Int: ''' Internal for type Anno '''
class Entity_Ext: ''' External for type Anno '''


    

class _ol_func_item():
    ''' Container for a function & it's evaluation '''

    def __init__(self,func,key=None,**kwargs):
        self.func          = func
        self.key           = key
        self.filter_kwargs = kwargs
        
    def execute(self, container, this_entity:Entity, other_entity:Entity, *args,**kwargs):
        return self.func(container,this_entity, other_entity, *args,**kwargs)

    def match(self,this_entity:Entity,other_entity:Entity):
        raise Exception('Child class expected to handle this')
    
    @classmethod
    def _wrapper(cls, parent, key=None, *args,**kwargs):
        ''' Wrapper to Intake info with resolve as:
            un-nest w/a
            attach to parent (OL_Container)
            return a _method[original_function] '''
        def wrapper[F](func:F)->F:

            if isinstance(func,(_ol_func_item_deliver,_ol_func_item_recieve)):
                func = func.func
            elif isinstance(func,OL_Container):
                func = func._origin_func
            
            inst = cls(func,*args,**kwargs)
            parent.add_func_container(inst)
            if key: parent.add_func_direct(key,inst)
            
            return _method(func)

        return wrapper

class _ol_func_item_recieve(_ol_func_item):
    ''' Ext -- calling -> Int '''

    def match(self,this_entity:'Entity_Int',other_entity:'Entity_Ext'):
        assert this_entity.Is_Int
        assert other_entity.Is_Ext
        ... #TODO

class _ol_func_item_deliver(_ol_func_item):
    ''' Int -- calling -> Ext '''
    
    def match(self,this_entity:'Entity_Ext',other_entity:'Entity_Int'):
        assert this_entity.Is_Ext
        assert other_entity.Is_Int
        ... #TODO

from copy import copy

class _def_dict_list(dict):
    def __missing__(self,key):
        self[key] = res = []
        return res

class OL_Container():
    ''' OL func Container, ie a contextual router that contains _ol_func_items. 
    Must have 'view' made when instancing parent
    Prob way more effecient & safe than forcing partial or setting a context va every access '''

    def __init__(self, func, path, *args,**kwargs):
        self._origin_func = func
        self._path        = path
        self._f_args      = args
        self._f_kwargs    = kwargs
        self._container   = None
        self._reciever_functions   = _def_dict_list()
        self._delivery_functions   = _def_dict_list()

    @classmethod
    def _on_new(cls,inst):
        ''' Utility, Call on new item to setup 'views' (local shallow copies w/ one var change) '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if isinstance(v,cls):
                if not (v._container is inst): 
                    setattr(inst,k,v._view(inst))

    def _view(self,container):
        new = copy(self)
        new._container = container
        return new
    
    def __call__(self, other_entity, request=None, *args, **kwargs):
        ''' Unfortunatly does require other entity to be declared as far as I can tell '''
        this_entity = self._container.Root_Entity
        recieving = this_entity.Is_Internal

        if recieving:
            assert request is not None 
            func = self.find_recieving (this_entity,other_entity,request)
            return func(self._container, this_entity, other_entity, *args, **kwargs)
        else: 
            func = self.find_delivering(this_entity,other_entity)
            return func(self._container, this_entity, other_entity, request, *args, **kwargs)
        
    def add_func_container(self,func_item:_ol_func_item):
        if   isinstance(func_item,_ol_func_item_deliver):
            self._delivery_functions.append(func_item)
        elif isinstance(func_item,_ol_func_item_recieve):
            self._reciever_functions.append(func_item)

    def add_func_direct(self,key,func):
        if hasattr(self,key):
            raise Exception(f'{self} SETUP ERROR: "{key}" already in use by {getattr(self,key)}' )
        setattr(self,key,func)

    @wraps(_ol_func_item_recieve._wrapper)
    def Get_Recieve(self,*args,**kwargs):
        return _ol_func_item_recieve._wrapper(parent=self,mode=Command.GET,*args,**kwargs)

    @wraps(_ol_func_item_deliver._wrapper)
    def Get_Deliver(self,*args,**kwargs):
        return _ol_func_item_deliver._wrapper(parent=self,mode=Command.GET,*args,**kwargs)

class Interface_Base():
    def __new__(self,):
        OL_Container._on_new(self)
        Interface_Base._on_new(self)
    
    def __init__(self, parent : 'Entity'|'Interface_Base'):
        self._parent = parent
        self._Root_Entity = parent._Root_Entity

    @staticmethod
    def _on_new(inst):
        ''' Intialize Interface Structure '''
        for k in [x for x in dir(inst) if not x.startswith('_')]:
            v = getattr(inst,k)
            if not isclass(v):
                continue
            if issubclass(v,Interface_Base):
                setattr(inst,k,v(inst))

class Entity(Interface_Base):
    
    def __init__(self):
        self._Root_Entity = self

    Entity_State          : Enum | _UNSET           = _UNSET
    Connection_State      : Enum | _UNSET | PRIMARY = _UNSET
    # Entity_Observed_Connection_State : dict[Enum]
        # What each connection assigns state to self w/a
        # Offset into connection?