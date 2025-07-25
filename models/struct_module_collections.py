

from .struct_module import ver_expr,module,_item_base,_mixin_base
from .struct_file_io import BaseModel
import copy

class _unset:...

class global_module_collection():
    '''Global module collection, all loaded modules preconstruction'''
    
    defaults : dict[str,str]
        #Populated by load, consumed by local_modules on instance. Replaced by file_io when loading w/a

    def __init__(self):
        self.defaults   = {}
        self.modules    = []

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
        self.modules.extend(module_list)

    def __iter__(self):
        for x in self.modules:
            yield x

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
    

Global_Module_Pool = global_module_collection()
    #Singleton, Consider different solution later


class local_module_collection(BaseModel):
    ''' Module collection used in construction of the graph and internal types '''
    allowed_modules:dict

    _io_whitelist_ = ['module_iten']
    G_Col = Global_Module_Pool

    module_iten : dict[str,str]
    modules     : list[module]


    def __init__(self, module_iten:dict = None):
        self.modules = []
        
        if self.allowed_modules is None:
            self.module_iten = copy.copy(self.G_Col.defaults)
        else:
            self.module_iten = module_iten

    def set_modules(self):
        ret = []
        for k,v in self.allowed_modules:
            if module:=self.G_Col[k,v]:
                ret.append(module)
        self._orig_modules = ret

    def check_deps(self):
        uids = []
        for mod in self.modules:
            for statement in mod.Deps:
                self.verify_statement(statement)
                self.verify_statement(statement,context_statement=f'On Module {mod.UID}({mod.Version})')
            assert mod.UID not in uids
            uids.append(mod.UID)
        for item in self.items:
            for statement in item.Deps:
                self.verify_statement(statement,context_statement=f'On Module Item {item.Module.UID}({item.Module.Version}) : {item.UID}({item.Version})')
            
    
    def verify_statement(self,statement,context_statement=''):
        mode,uid,ver,message = statement
        mode = mode.lower()
        res = self[(uid,ver)]
        if   mode == 'required' and not res: raise Exception(f'Module Loader {mode} Dependencies Statement Failed {context_statement} : {message}') 
        elif mode == 'incompatable' and res: raise Exception(f'Module Loader {mode} Dependencies Statement Failed {context_statement} : {message}')
        elif mode == 'warning'      and res: print(f'Module Loader {mode} Dependencies Statement Failed {context_statement} : {message}')
        elif mode == 'enable_if_any':   ...
        elif mode == 'enable_if_all':   ...
            #TODO: enable_if is item exclusive. Enforce inside statment somehow. 
        else: raise Exception(f'Module Loader {mode} is not ')
    
    def item_statements_enabled(self,item)->bool:
        ''' Determine if an item should be enabled to be added based on statements'''
        any_statements = []
        all_statements = []

        for statement in item.Deps:
            if statement[0].lower() == 'enable_if_any':
                any_statements.append(self.item_statement_enabled(self,statement))
            elif statement[0].lower() == 'enable_if_all':
                all_statements.append(self.item_statement_enabled(self,statement))
        
        if all_statements:
            all_res = all(all_statements)
        else:
            all_res = True
        
        if any_statements:
            any_res = any(any_statements)
        else:
            any_res = True
        
        return any_res and all_res

    def item_statement_enabled(self,statement,context_statement='')->bool:
        #enabled_if is implicitly an AND rather than an or. 
        mode,uid,ver,message = statement
        mode = mode.lower()
        res = self[(uid,ver)]
        return True if res else False


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
        ''' Filter allowed items with statement evaluation '''
        _ret = []
        ret  = []
        for x in self.modules:
            _ret.extend(x._loader_items_)
        for x in _ret:
            if self.item_statements_enabled(x):
                ret.append(x)
        return ret

    def items_by_attr(self,attr,value)->list[_item_base]:
        ret = []
        for x in self.items:
            if getattr(x,attr,_unset) == value:
                ret.append(x)
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

    