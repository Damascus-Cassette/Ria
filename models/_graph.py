from ._base_node import base_node, base_node_collection
from .struct_context import context
from .struct_file_io import flat_col, flat_ref, BaseModel, defered_archtype
import copy

# from .modules import module_collection

from typing import Any

from .__loader import loader

from .__meta_subgraph import meta_subgraph_collection

from .__exec_subgraph import exec_subgraph


class _delayed_exec_node_archtype():... #These are placeholders
class _delayed_meta_node_archtype():... #These are placeholders
class _delayed_modules_archtype()  :... #These are placeholders
class graph(BaseModel):
    _exec_nodes, _meta_nodes, _modules = loader.construct()
    
    meta_subgraphs = meta_subgraph_collection
    exec_subgraph  = exec_subgraph

    exec_nodes : flat_col['exec_nodes',_delayed_exec_node_archtype] #placeholders
    meta_nodes : flat_col['meta_nodes',_delayed_meta_node_archtype] #placeholders
    modules    : flat_col['modules'   ,_delayed_modules_archtype  ] #placeholders

    enabled_modules : list[str]

    def __init__(self):

        self.loader = loader.construct()
        self.meta_subgraphs = self.meta_subgraphs.construct()
        self.exec_subgraph  = self.exec_subgraph.construct()

        self.__orig_cols = copy.copy(self.__orig_cols)
        self.__orig_cols['exec_nodes'] = flat_col('exec_nodes',self.loader._exec_nodes)
        self.__orig_cols['meta_nodes'] = flat_col('meta_nodes',self.loader._meta_nodes)
        self.__orig_cols['modules']    = flat_col('modules',self.loader._modules)

    def _import_(self,data):
        if 'enabled_modules' in data.keys()
            modules = data['enabled_modules']
        else:
            modules = None
        self.loader.load(enabled = modules)
        self.super()._import_(data)

    context = context.construct(include=['graph_collection'],as_name='graph')
    def _walk_context_(self):
        with self.context.register():
            for sg in self.meta_subgraphs:
                sg._walk_context_()