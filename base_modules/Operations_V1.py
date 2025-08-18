#Module to alllow for copy-pasting objects.

from ..models.struct_module import module, module_test
from ..models.base_node     import socket_group
from .Execution_Types       import _mixin, item
# from .Execution_Types       import socket_shapes as st

from typing                 import Any, Self, TypeAlias,AnyStr,Type
from types                  import FunctionType, LambdaType
from inspect                import isclass

class main():
    ''' Module for adding copy (and eventually more) functionality that respects structure contextually.
    Will be merged with base_structure perm after initial testing, and hooks will be set after structure settles
    
    Extra relevent info:
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

    class subgraph_mixin(_mixin.subgraph):
        def copy_in_node():
            ...
        def copy_in_nodes(self, nodes, keep_links=True,return_memo=True,memo=None)->tuple[item.node]:
            '''copy in nodes from any subgraph, uses self.nodes.copy_in_multi with local_copy as true 
            Allows 'blind' nodes w/out context having been walked
            Initilizes context structure after copying in.
            '''

            new_nodes, memo = self.nodes.copy_in_multi(nodes,local_copy=True,return_memo=True,memo=memo)
            if keep_links:
                links = []
                subgraphs = set([x.context.subgraph for x in nodes if x.context.subgraph is not None])
                for sg in subgraphs:
                    links.extend([l for l in sg.links if ((l.from_node in nodes) and (l.to_node in nodes)) ])
                new_links,memo = self.links.copy_in(links, local_copy=True,return_memo=True, memo=memo)
                with self.context.Cached():
                    for x in new_links:
                        x._context_walk_()
            
            with self.context.Cached():
                for x in new_nodes:
                    x._context_walk_()

            if return_memo: return  new_nodes,memo
            return new_nodes

        def copy_walk(self,dir:str|tuple=('in','side','out'),return_memo=False,memo=None):
            #Walk all related nodes in the direction to prep for copy.
            ...

    class node_mixin(_mixin.node):
        def walk(self,dir:str|tuple=('in','side','out'),chain=None, filter:LambdaType=None, return_links=False)->tuple[item.node]|tuple[tuple[item.node],tuple[item.link]]:
            ''' Recursive directional walk, returns a list of nodes, optionaly also returns links'''
            if chain is None: chain = []
            
            

    # class socket_mixin(_mixin.socket):
    #     ...
    # class link_mixin(_mixin.link):
    #     ...
