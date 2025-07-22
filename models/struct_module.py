from . import base_node as _base_node 
from typing import Any
from inspect import isclass

class _mixin_base:
    ''' Mixes into all specified's base class 
        For hooking and base behavior changes '''

    _loader_mixin_ = True
    _constr_asbase_discard_ = True
    Module_Id : str
    Module_V  : str

class _item_base:
    ''' Is a new node class, for execution and hooks 
        Note: inherits all node_mixins from all enabled modules'''
    _loader_item_ = True
    
    ID           : str
    Version      : str
    Label        : str
    Soft_Dependencies : list[str|tuple] 
        #use this node if x modules IDs and version are enabled

    def __init_subclass__(cls):
        assert getattr(cls, 'UID'    , None) is not None
        assert getattr(cls, 'Version', None) is not None
        assert getattr(cls, 'Label'  , None) is not None
        assert getattr(cls, 'Desc'  ,  None) is not None

class mixin:
    class node(_mixin_base,_base_node.node):...

class item:
    class node(_item_base,_base_node.node):...
    
class module():
    ''' Inherit onto base '''

    ID           : str
    Version      : str
    Label        : str
    Dependencies : list[str|tuple]
        #raise error if dependencies not found by loader

    _loader_mixins_ : list[Any]
    _loader_items_  : list[Any]

    def __init_subclass__(cls):
        assert getattr(cls,'UID',None)     is not None
        assert getattr(cls,'Version',None) is not None
        assert getattr(cls,'Label',None)   is not None
        assert getattr(cls,'Desc',None)    is not None

        cls._loader_items_  = getattr(cls,'_loader_items_',[])
        cls._loader_mixins_ = getattr(cls,'_loader_mixins_',[])

        for k,v in vars(cls):
            if not isclass(): 
                continue
            elif issubclass(v,_mixin_base):
                cls._loader_mixins_.append()
            elif issubclass(v,_item_base):
                cls._loader_items_.append()

class module_collection():
    
    def __init__():
        ...

    def append(self,):
        ...