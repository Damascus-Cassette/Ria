from packaging.version import Version as VersionType
from inspect import isclass
from typing import Any

class _mixin_base:
    ''' Mixes into all specified's base class 
        For hooking and base behavior changes '''

    _loader_mixin_ = True
    _constr_asbase_discard_ = True
    Module_Id : str
    Module_V  : str
    Deps         : list[tuple[str,str,str,str]] 
    Module       : Any

class _item_base:
    ''' Is a new node class, for execution and hooks 
        Note: inherits all node_mixins from all enabled modules'''
    _loader_item_ = True
    
    ID           : str
    Version      : str
    Label        : str
    Deps         : list[tuple[str,str,str,str]]
    Module       : Any 
        #use this node if x modules IDs and version are enabled

    def __init_subclass__(cls):
        assert getattr(cls, 'UID'    , None) is not None
        assert getattr(cls, 'Version', None) is not None
        assert getattr(cls, 'Label'  , None) is not None
        assert getattr(cls, 'Desc'  ,  None) is not None

        cls._Version = VersionType(cls.Version)
        cls.Version  = cls._Version.release

    
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
        
        cls._Version = VersionType(cls.Version)
        cls.Version  = cls._Version.release

        
        _mixins = cls.__module_set_components__(_mixin_base, '_loader_mixins_' )
        _items  = cls.__module_set_components__(_item_base,  '_loader_items_'  )
        print(f'ITEMS: {_items}')
        print(f'MIXINS: {_mixins}')
        for x in _items:
            x.Module = cls

    @classmethod
    def __module_set_components__(cls,type,attr)->None:
        print('Called Module Set Components!!') 
        if (res:=getattr(cls,attr,None)) is None:
            res = []
            for k,v in vars(cls).items():
                if not isclass(v): 
                    continue
                elif issubclass(v,type):
                    res.append(v)
            setattr(cls,attr,res)
        return res
        

class ver_expr():
    ''' Version compatability expression, such as '<5.3,>4.2,!4.41a,=4.2' 
    Using packaging.version.Version
    '''

    src_ops = list[tuple[str,VersionType]]

    def __init__(self,expr:str):
        self.src_ops = []
        src = [x.replace(' ','') for x in expr.split(',') if x]
        
        for x in src:
            split = x.split('(',1)
            assert split[1][-1] == ')'
            ops = split[0]
            val = split[1][0:-1]
            val = VersionType(val)

            for x in ops:
                self.src_ops.append((x,val))

    def __call__(self,version:VersionType):
        print(f'CALLED VER_EXPR {self.src_ops} WITH {version}')
        if isinstance(version,tuple):
            return all(self.ops(x[0], x[1].release, version) for x in self.src_ops)            
        elif not isinstance(version,VersionType):
            version = VersionType(version)
        return all(self.ops(x[0], x[1], version) for x in self.src_ops)
    
    def ops(self,op,src,check):
        assert op in self.operations
        if   op == '>': return src >  check 
        elif op == '<': return src <  check 
        elif op == '=': return src == check
        elif op == '!': return src != check
        # else: raise Exception(f'Expression in version check not accounted for : {op}')
    
    operations = ['>','<','=','!']

from collections import defaultdict

