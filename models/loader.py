## Should not be placed in models, where then?

# from .exec_node_defaults import exec_fallback
# from .meta_node_defaults import meta_fallback

from .struct_file_io import flat_col, flat_ref, BaseModel, defered_archtype

class _exec_nodes(defered_archtype): ... 
class _meta_nodes(defered_archtype): ... 
class _modules(defered_archtype): ... 
    #Defered archtypes used as placeholders to fill with defined types on load.