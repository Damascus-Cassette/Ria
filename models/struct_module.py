from packaging.version import Version as VersionType
from inspect import isclass
from typing import Any,Callable, ForwardRef
# from collections import defaultdict
from .struct_hook_base import Hookable

class _mixin_base(Hookable):
    ''' Mixes into all specified's base class 
        For hooking and base behavior changes '''

    _loader_mixin_ = True
    # _constr_asbase_discard_ = True
    Module_Id    : str
    Module_V     : str
    Deps         : list[tuple[str,str,str,str]] 
    Module       : Any

class _item_base(Hookable):
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
        if getattr(cls,'_module_verify_',False):
            assert getattr(cls, 'UID'    , None) is not None
            assert getattr(cls, 'Version', None) is not None
            assert getattr(cls, 'Label'  , None) is not None
            assert getattr(cls, 'Desc'  ,  None) is not None

            cls._Version  = VersionType(cls.Version)

        # cls.Version_R = cls._Version.release
        # cls.Version   = cls._Version.release

class module_test():
    ''' Consolidated test object, can allow implicit setup and loading of modules not directly defined. '''
    
    module : 'module' = None

    def __init__(self,test_name :str ,/,*,
                 module = None,
                #  implicit_load  :bool           = True,
                 module_iten    :dict           = None, 
                 funcs          :list[Callable] = None):
        self.name        = test_name
        self.module      = module
        self.module_iten = module_iten
        self.funcs       = funcs
        assert funcs is not None

    def intake_module(self,module:'module'):
        self.module = module
        if not self.module_iten:
            raise Exception('Implicit loading is not yet supported! Please Define Iten in Module_Test')
            # from .struct_module_collections import Global_Module_Pool
            # self.module_iten = Global_Module_Pool module.Dependencies

    def run_tests(self,m_graph):
        for x in self.funcs:
            key = f'{self.module.UID} Test: {self.name} : {x.__name__}'
            graph     = m_graph.graphs.new(key         = key,
                                           label       = key,
                                           module_iten = self.module_iten,
                                           )
            m_graph._Set_As_Active_Construction(graph)
            subgraph = graph.subgraphs.new('test_env')
            x(graph,subgraph)

    
class module():
    ''' Inherit onto base '''

    ID           : str
    Version      : str
    Label        : str
    Dependencies : list[str|tuple]
        #raise error if dependencies not found by loader

    _loader_mixins_ : list[Any]
    _loader_items_  : list[Any]
    
    _module_tests_  : list[module_test]

    def __init_subclass__(cls):
        assert getattr(cls,'UID',None)     is not None
        assert getattr(cls,'Version',None) is not None

        cls._module_tests_  = getattr(cls,'_module_tests_',[])
        
        cls.Label = getattr(cls,'Label',f'({cls.UID}:{cls.Version})')
        cls.Desc  = getattr(cls,'Desc',cls.__doc__)

        cls._Version = VersionType(cls.Version)

        _mixins = cls.__module_set_components__(_mixin_base, '_loader_mixins_' )
        _items  = cls.__module_set_components__(_item_base,  '_loader_items_'  )    

        for x in _items:
            x.Module = cls

        for x in getattr(cls,'_module_tests_',[]):
            x.intake_module(cls)
        super.__init_subclass__()

    @classmethod
    def __module_set_components__(cls,type,attr)->None:
        if (res:=getattr(cls,attr,None)) is None:
            res = []
            for k,v in vars(cls).items():
                if not isclass(v): 
                    continue
                elif issubclass(v,type):
                    res.append(v)
            setattr(cls,attr,res)
        return res
    
    @classmethod
    def _run_tests(cls,m_graph):
        for test_obj in getattr(cls,'_module_tests_',[]):
            test_obj.run_tests(m_graph)
            

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


