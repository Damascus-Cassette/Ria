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

        for k,v in vars(cls).items():
            if not isclass(v): 
                continue
            elif issubclass(v,type):
                print(v, 'IS OF TYPE', type)
                res.append(v)
                v.Module = cls
        setattr(cls,attr,res)
        

class ver_expr():
    ''' Version compatability expression, such as '<5.3,>4.2,!4.41a,=4.2' 
    TODO: Switch to packaging.version.parse instead of standard!
    '''
    src_indv : list[str]
    src_expr : str

    def __init__(self,expr:str):
        src = [x.replace(' ','') for x in expr.split(',') if x ]
        self.src_expr = expr
        self.src_indv  = src

    def __call__(self,evaluated_Version):
        return all([self.check_indv(x,evaluated_Version) for x in self.src_indv])
    
    def check_indv(self,check,src)->bool:
        ''' Breach each into a numerical set, check if expression matches '''
        ''' 4.1a > 3.1b via split to digit, zfill, append, then regular string operands '''        
        s_num, s_stg, _     = self.standard(src)
        c_num, c_stg, c_ops = self.standard(check)

        if len(s_num) > len(c_num):
            c_num = c_num.zfill(len(s_num))
        elif len(s_num) < len(c_num):
            s_num = s_num.zfill(len(c_num))
        
        print(c_num,c_stg)
        print(s_num,s_stg)
        c_num = str(c_num) + c_stg
        s_num = str(s_num) + s_stg
        
        assert c_ops

        val = [self.ops(x,c_num,s_num) for x in c_ops]
        print('RESULT IS:',c_num,s_num, {c_ops[i]:val[i] for i in range(len(val))})
        val = all(val)
        
        return val
    
    def standard(self,check:str)->list[str,str|int,str]:
        num = ''.join([x for x in check if x.isdigit()])
        stg = ''.join([x for x in check if x.isalnum() and not x.isdigit()])
        ops = ''.join([x for x in check if not x.isalnum() and not x == '.'])
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

