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

        cls.__module_components__(_mixin_base,'_loader_mixins_')
        cls.__module_components__(_item_base,'_loader_items_')

    @classmethod
    def __module_components__(cls,type,attr)->None:
        if getattr(cls,attr,None) is not None:
            return
        for k,v in vars(cls):
            if not isclass(): 
                continue
        res = []
        for k,v in vars(cls):
            if not isclass(): 
                continue
            elif issubclass(v,type):
                res.append()
        setattr(cls,attr,res)
        return        

class ver_expr():
    ''' Version compatability expression, such as '<5.3,>4.2,!4.41a,=4.2' '''
    src_indv : list[str]
    src_expr : str

    def __init__(self,expr:str):
        src = [x.replace(' ','') for x in expr.split(',') if x ]
        self.src_expr = expr
        self.src_indv  = src

    def __call__(self,evaluated_Version):
        return all([self.check_indv(x,evaluated_Version) for x in self.src_indv])
    
    def check_indv(self,src,check)->bool:
        ''' Breach each into a numerical set, check if expression matches '''
        ''' 4.1a > 3.1b via split to digit, zfill, append, then regular string operands '''        
        s_num, s_stg, _     = self.standard(src)
        c_num, c_stg, c_ops = self.standard(check)

        if len(s_num) > len(c_num):
            c_num = c_num.zfill(len(s_num))
        elif len(s_num) > len(c_num):
            s_num = s_num.zfill(len(c_num))
        
        c_num = c_num.append(c_stg)
        s_num = s_num.append(s_stg)

        assert c_ops

        return all([self.ops(x,c_num,s_num) for x in c_ops])
    
    def standard(self,check:str)->list[str,str|int,str]:
        num = str([x for x in check if x.isdigit])
        stg = str([x for x in check if x.isascii])
        ops = str([x for x in check if (not x.isascii) and (not x.isdigit)])
        ops = ops.replace('!=','!')
        return (num, stg, ops)
    
    def ops(self,op,src,check):
        assert op in self.operations
        if   op == '>': return src >  check 
        elif op == '<': return src <  check 
        elif op == '=': return src == check
        elif op == '!': return src != check
        # else: raise Exception(f'Expression in version check not accounted for : {op}')
    
    operations = ['>','<','=','!']

class global_module_collection():
    '''Global module collection, all loaded modules preconstruction'''

    def __init__(self):
        self.modules = []

    def __getitem__(self,key:str|tuple[str,str|ver_expr])->tuple[module]|module:
        if isinstance(key,str):
            return self.find_by_uid(key)
        elif isinstance(key,tuple):
            if key[1].startswith(tuple(ver_expr.operations)):
                subset = self.find_by_uid(key[0])
                expr   = ver_expr(key[1])
                return self.filter_by_expr(subset,expr)
            else:
                subset = self.find_by_uid(key[0])
                for module in subset:
                    if module.Version == key[1]:
                        return module

    def find_by_uid(self,uid):
        res = []
        for x in self.modules:
            if x.UID == uid:
                res.append(x)
        return res

    def filter_by_expr(self,subset, expr:str):
        res = []
        for mod in subset:
            if expr(mod.Version):
                res.append(mod)
        return res

    def append(self,module):
        self.modules.append(module)

    def extend(self,module_list):
        self.modules.extend(module)

    def __iter__(self):
        for x in self.modules:
            yield x
            
class local_module_collection():
    ''' Module collection used in construction of the graph and internal types '''
    allowed_modules:dict
    modules : list[module]
    def __init__(self,g_col:global_module_collection, allowed_modules:dict = None):
        self.modules = []
        self.g_col        = g_col
        self.allowed_modules = allowed_modules

    def set_modules(self):
        ret = []
        for k,v in self.allowed_modules:
            if module:=self.g_col[k,v]:
                ret.append(module)

    def check_deps(self):
        uids = []
        for mod in self.modules:
            for statement in mod.Dependencies:
                self.verify_statement(statement)
            assert mod.UID not in uids
            uids.append(mod.UID)
    
    def verify_statement(self,statement):
        mode,uid,ver,message = statement
        mode = mode.lower()
        res = self[(uid,ver)]
        if   mode == 'required' and not res: raise Exception(f'Module Loader {mode} Dependencies Statement Failed: {message}') 
        elif mode == 'incompatable' and res: raise Exception(f'Module Loader {mode} Dependencies Statement Failed: {message}')
        elif mode == 'warning'      and res: print(f'Module Loader {mode} Dependencies Statement Failed: {message}')
        else: raise Exception(f'Module Loader {mode} is not ')

    def __getitem__(self,key:str|tuple[str,str|ver_expr])->tuple[module]|module|None:
        if isinstance(key,str):
            return self.find_by_uid(key)
        elif isinstance(key,tuple):
            if key[1].startswith(tuple(ver_expr.operations)):
                subset = self.find_by_uid(key[0])
                expr   = ver_expr(key[1])
                return self.filter_by_expr(subset,expr)
            else:
                subset = self.find_by_uid(key[0])
                for module in subset:
                    if module.Version == key[1]:
                        return module

    def find_by_uid(self,uid):
        res = []
        for x in self.modules:
            if x.UID == uid:
                res.append(x)
        return res

    def filter_by_expr(self,subset, expr:str):
        res = []
        for mod in subset:
            if expr(mod.Version):
                res.append(mod)
        return res
    
    def append(self,item:tuple|module):
        if isinstance(item,tuple):
            self.allowed_modules[item[0]] = item[1]
        else:
            self.modules.append(item)

    def extend(self,module_list):
        for x in module_list:
            self.append(x)

    @property
    def items(self)->list[_item_base]:
        ret = []
        for x in self.modules:
            ret.extend(x._loader_items_)
        return ret

    @property
    def mixins(self)->list[_mixin_base]:
        ret = []
        for x in self.modules:
            ret.extend(x._loader_mixins_)
        return ret

    def __iter__(self):
        for x in self.modules:
            yield x