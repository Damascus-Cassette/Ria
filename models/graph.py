from .base_node import base_node, base_node_collection
from .struct_context import context
from .struct_file_io import flat_col, flat_ref, BaseModel, defered_archtype


# from .modules import module_collection

from typing import Any

from .loader import (_exec_nodes,
                     _meta_nodes,
                     _modules)

from .meta_subgraph import meta_subgraph_collection

from .exec_subgraph import exec_subgraph


class graph(BaseModel):
    meta_subgraphs : flat_col['subgraph',Any] = meta_subgraph_collection.construct() #type:ignore
    exec_subgraph  : exec_subgraph

    context = context.construct(include=['graph_collection'],as_name='graph')
    def _walk_context_(self):
        with self.context.register():
            for sg in self.meta_subgraphs:
                sg._walk_context_()

    def __init__(self):
        self.context = self.context(self)
        self.meta_subgraphs = self.nodes()