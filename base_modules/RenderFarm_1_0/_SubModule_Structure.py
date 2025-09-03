from .backwards_context           import Backwards_Context
from ..Execution_Types          import item, _mixin, socket_shapes
from ..utils.print_debug        import debug_print_wrapper
from ...statics                 import _unset
from ...models.struct_hook_base import hook, hook_trigger,Hookable
from ...models.struct_module    import module_test
from ...models.base_node        import (subgraph            as _subgraph_base,
                                        node_collection     as _node_collection_base,
                                        subgraph_collection as _subgraph_collection_base,)


from contextvars import ContextVar
from contextlib  import contextmanager
from typing      import Any, Self
from types       import FunctionType
from enum        import Enum


class exec_node_collection(_node_collection_base):
    ''' Merging done by operations on subgraph, Only exists to assert exec_nodes and call merge as required. '''
    @property
    def Bases(self)->dict[str,Any]:
        res = self.context.root_graph.module_col.items_by_attr('_constr_bases_key_','node:exec')
        return res

    _coll_merge_on_setitem_ : bool = True
    _coll_mergeable_base_   : bool = True 
        #Should be contextual to allow for monadish?
        #May interfere with op to op, could rely on resulting behavior instead of rigid internal definition.

    def _coll_merge_handler_(self,left,right):
        #Assert same structural key, else throw error?
        left.merge(right)
        return left
    

class exec_subgraph(_subgraph_base):
    ''' Execution subgraph, changes base for exec_node_collection '''
    
    Nodes_Base = exec_node_collection
    
    # memo : Memo

    @hook('__init__',mode='pre')
    def _init_hook_(self):
        ...
        # self.memos = Memo()

class exec_subgraph_collection(_subgraph_collection_base):
    Base = exec_subgraph


class meta_subgraph_mixin(_mixin.graph):
    exec_subgraphs : exec_subgraph_collection
    
    @hook(event ='__init__', mode='pre', see_args=True)
    def _init_(self,*args,**kwargs):
        self.exec_subgraphs = exec_subgraph_collection()


######## TESTS ########



def test_structure(graph,subgraph):
    assert hasattr(graph,'exec_subgraphs')

_structure_test = module_test('Exec_Node_Tests',
    module      = None,
    funcs       = [
        test_structure,
    ],
    module_iten = { 'Distributed_Execution' : '1.0'}, 
    )


_structure_mixins_ = [meta_subgraph_mixin]
_structure_tests_  = [_structure_test]
_structure_items_  = []