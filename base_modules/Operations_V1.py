#Module to alllow for copy-pasting objects.

from ..models.struct_module import module, module_test
from ..models.base_node     import socket_group
from .Execution_Types       import _mixin, item
# from .Execution_Types       import socket_shapes as st

from typing                 import Any, Self, TypeAlias,AnyStr,Type
from types                  import FunctionType
from inspect                import isclass

class main():
    ''' Module for adding copy (and eventually more) functionality that respects structure contextually.
    May be merged with base_structure perm
    '''
    ''' Extra relevent info:
    - Context has __deepcopy__ return a shallow copy
    - Any Execution Module being used should determine how processed values are stored and deepcopied.
    - In general: object references should be within a pointer container that returns a shallow copy of self.
    - Directy deepcopied collection items still need to be re-attached a parent collection.
    - Add copy method to collection for deepcopy with localizing.
    - Links between subgraphs are not supported.
    - Want to find distinct term for copying vs moving vs copy-moving between collections 
    '''
    UID     = 'Operations'
    Version = '1.0'

    class node_mixin(_mixin.node):
        ...
    class socket_mixin(_mixin.socket):
        ...
    class link_mixin(_mixin.link):
        ...
    class subgraph_mixin(_mixin.subgraph):
        ... 

    class node_collection_mixin(_mixin.node_collection):
        ...
    class node_collection_mixin(_mixin.link_collection):
        ...