''' 
Take in a list of module IDs, 
mount onto deep copied base_graph.py, 
return copied and constructed graph
Used by meta_graph
Consider as statefull instance that allows re-loading of modules (store bases pre-post construction?).
'''

from copy import deepcopy
from .struct_module import (global_module_collection,
                            local_module_collection)
from ..base_modules import modules  as base_modules
from ..base_modules import defaults as base_module_defaults
from . import base_node 
import copy
# will have another that loads user modules here as well

Global_Module_Pool = global_module_collection()
Global_Module_Pool.extend(base_modules)
# Global_Module_Pool.extend(user_modules)

class graph_module_loader():
    ''' Construct a copy of the base_node class, hold reference for re-construction and similar. '''
    
    module_iten : dict[str,str|int]
    loaded  : base_node

    def __init__(self,module_iten:dict=None):
        if module_iten is None: module_iten = {}|base_module_defaults
        self.module_iten = module_iten

    def load(self)->base_node:
        ''' Construct a new loaded graph'''
        module_col = local_module_collection(Global_Module_Pool, allowed_modules=copy.copy(self.module_iten))
        base_node.module_col = module_col
            #local_module_collection has custom __deepcopy__ func to only construct the mixins & items
        
        new_base_node = deepcopy(base_node)
            #Split tree to allow different modules per.

        new_base_node.construct()
        new_base_node.loader = self

        self.loaded = new_base_node
        return new_base_node

    def reload(self):
        ''' Replace modules, reconstruct. But node type and version conversion is unknown currently. 
            Could be better suited on the graph instance itself
        '''
        # self.loaded.module_col.allowed_modules = self.module_iten
        # self.loaded.Construct()
        # for graph in self.loaded.graph_users:
            # self.loaded.users.Reload()

        
    