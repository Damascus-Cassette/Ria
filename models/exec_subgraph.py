from .base_node import base_node, base_node_collection
from .struct_context import context
from .struct_file_io import flat_col, flat_ref, BaseModel, defered_archtype

from exec_node import exec_node_collection

class exec_subgraph(BaseModel):
    ''' singular subgraph used for the flattened exec_nodes '''

    nodes : base_node_collection = exec_node_collection.construct() #type:ignore
    
    context = context.construct(include=['graph'],as_name='subgraph')
    def _walk_context_(self):
        with self.context.register():
            for node in self.nodes:
                node._walk_context_()

    def __init__(self):
        self.nodes = self.nodes()
        self.context = self.context(self)