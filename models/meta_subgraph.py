from .base_node import base_node, base_node_collection
from .struct_context import context
from .struct_file_io import flat_col, flat_ref, BaseModel, defered_archtype

from .loader import _meta_nodes, _modules

class meta_subgraph(BaseModel):
    ''' One of a number of subgraphs who's nodes can have cross-references '''
    nodes : flat_col['meta_node',_meta_nodes] = base_node_collection.construct() #type:ignore
    # modules : flat_col['modules'  ,_modules   ] = module_collection.construct()
    
    context = context.construct(include=['graph'],as_name='subgraph')
    def _walk_context_(self):
        with self.context.register():
            for node in self.nodes:
                node._walk_context_()
                
    def __init__(self):
        #no need to do with here as no defaults, On import I will have to do 'with self.context.register():'
        self.context = self.context(self)
        self.nodes = self.nodes()
        # self.modules = self.modules()
    

class meta_subgraph_collection(dict):
    ...
