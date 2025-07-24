from typing import Any
from inspect import isclass

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

        cls.__module_set_components__(_mixin_base,'_loader_mixins_')
        cls.__module_set_components__(_item_base,'_loader_items_')

    @classmethod
    def __module_set_components__(cls,type,attr)->None:
        res = []
        for k,v in vars(cls):
            if not isclass(): 
                continue
            elif issubclass(v,type):
                res.append()
                v.Module = cls
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

from collections import defaultdict

class meta_graph(BaseModel, ConstrBase):
    ''' Should have a single instance, holds graphs, sets active. If more than one instance the latest active's modules are used. '''
    ''' Current design limitation of structure for flexibility to instnace manually in user modules. '''
    _constr_call_post_ = ['__io_setup__']
    _constr_bases_key_ = 'metagraph'
    Global_Module_Pool = Global_Module_Pool

    def _Set_As_Active_Construction(self,graph_inst:graph):
        ''' Construct in place all types using modules list '''
        ''' This does limit the active graph count to 1, Non-active graphs will have to'''

        module_col = graph_inst.module_col
        assert graph_inst.active
        
        mixins = defaultdict(dict)
        for x in module_col.mixins:
            key = getattr(x,'_constr_bases_key_','_uncatagorized')
            mixins[key] = x

        with Bases.set(mixins):
            pointer_socket.Construct(recur=False)
            socket.Construct(recur=False)
            socket_group.Construct(recur=False)
            socket_collection.Construct(recur=False)
            node.Construct(recur=False)
            node_collection.Construct(recur=False)
            subgraph.Construct(recur=False)
            subgraph_collection.Construct(recur=False)
            graph.Construct(recur=False)
            self.__class__.Construct(recur=False)



def _Load_Types():
    items  = defaultdict(dict)

    for x in global_module_col.items:
        key = getattr(x,'_constr_bases_key_','_uncatagorized')
        items[key] = x

    node_archtype   = items['node']
    socket_archtype = items['socket']
