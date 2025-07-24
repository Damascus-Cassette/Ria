''' 
Load modules into the Global_Module_Pool singleton.
This will be the place to re-load when I figure out the implications
After re-loading and re-populating the Global_Module_Pool the nodes will need to be re-constructed.
'''

from copy import deepcopy
from .struct_module_collections import (local_module_collection, Global_Module_Pool)

def load(): 
    from ..base_modules import modules  as base_modules
    from ..base_modules import defaults as base_module_defaults
    # will have another that loads user modules here as well
    Global_Module_Pool.extend(base_modules)
    Global_Module_Pool.defaults = base_module_defaults

load()

        
    