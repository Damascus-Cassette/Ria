''' 
Take in a list of module IDs, 
mount onto deep copied base_graph.py, 
return copied and constructed graph
Used by meta_graph
Consider as statefull instance that allows re-loading of modules (store bases pre-post construction?).
'''

from copy import deepcopy
from ..base_modules import modules as base_modules
from . import base_node 
# will have another that loads user modules here as well


class graph_module_loader():
    ''' Construct a copy of the base_node class '''
    
    loaded : base_node
    module_id_list : list[str]

    def __init__(self, module_id_list:list[str]):
        self.module_id_list = module_id_list

    def load(self)->base_node:
        modules = [x for x in base_modules if x.UID in self.module_id_list]
        base_node.modules = modules
        new_base_node = deepcopy(base_node)
        new_base_node.construct()
        base_node.modules = []
        return new_base_node

    def reload():
        ...
    