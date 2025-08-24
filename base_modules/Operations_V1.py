#Module to alllow for copy-pasting objects.

from ..models.struct_module import module, module_test
from ..models.base_node     import socket_group
from .Execution_Types       import _mixin, item
# from .Execution_Types       import socket_shapes as st

from typing                 import Any, Self, TypeAlias,AnyStr,Type
from types                  import FunctionType, LambdaType
from inspect                import isclass

class main(module):
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
        def find_links_in_node_pool(self, nodes):
            ''' Find all links between input iterable of nodes, regaurdless of subgraph '''
            links = []
            subgraphs = set([x.context.subgraph for x in nodes if x.context.subgraph is not None])
            for sg in subgraphs:
                links.extend([l for l in sg.links if ((l.from_node in nodes) and (l.to_node in nodes)) ])
            return links

        def copy_in_nodes(self, nodes,links=None, keep_links=True,return_memo=True,memo=None,filter=None)->tuple[item.node]:
            '''copy in nodes from any subgraph, uses self.nodes.copy_in_multi with local_copy as true 
            Allows 'blind' nodes w/out context having been walked
            Initilizes context structure after copying in.
            '''

            new_nodes, memo = self.nodes.copy_in_multi(nodes,local_copy=True,return_memo=True,memo=memo,filter=filter)
            if keep_links:
                if links is None:
                    links = self.find_links_in_node_pool(nodes)
                new_links,memo = self.links.copy_in_multi(links, local_copy=True,return_memo=True, memo=memo,filter=filter)

                with self.context.Cached():
                    for x in new_links:
                        x._context_walk_()
            
            with self.context.Cached():
                for x in new_nodes:
                    x._context_walk_()

            if return_memo: return  new_nodes,memo
            return new_nodes

        def copy_walk(self,
                      headers         : tuple[item.node]|item.node,
                      dir             : str|tuple       = ('in','side','out'),
                      dir_constrained : bool            = False,
                      return_memo     : bool            = False, 
                      memo            : dict[str,Any]   = None,
                      filter          : LambdaType|None = None,
                      ):
            ''' Walk_in with a direction, copy nodes and copy-convert links '''
            if not isinstance(headers,(tuple,list,set)):
                headers = (headers,)
            
            nodes = []
            links = []
            chain = []

            for node in headers:
                _ns,_ls = node.walk(direction = dir,chain=chain,dir_constrained =dir_constrained, return_links = True, filter = filter)
                nodes.extend(_ns)
                links.extend(_ls)
            return self.copy_in_nodes(nodes=nodes, links=links, keep_links=True, return_memo=return_memo, memo=memo)

    class node_mixin(_mixin.node):
        def walk(self,
                 direction       :str|tuple  = ('in','side','out'),
                 chain           :list       = None  ,
                 dir_constrained :bool       = False , 
                 filter          :LambdaType = None  , 
                 return_links    :bool       = False ,
                 )->tuple[item.node]|tuple[tuple[item.node],tuple[_mixin.links]]:
            ''' Recursive directional walk, returns a list of nodes, optionaly also returns links'''
            if chain is None: chain = []
            if filter is None: filter = lambda *args: True 
            res_nodes = []
            res_links = []

            def _walk_coll(fallback,collection):
                if dir_constrained: _dir = (fallback,)
                else:                     _dir = direction
                for n,l in collection.other_nodes(yield_links=True):
                    if not filter(self,n,l): continue
                    
                    if return_links:
                        _nodes,_links = n.walk(_dir,chain,dir_constrained,filter,return_links)
                        res_links.append(l)
                        res_nodes.extend(_links)
                        res_nodes.extend(_nodes)
                    else:
                        _nodes        = n.walk(_dir,chain,dir_constrained,filter,return_links)
                        res_nodes.extend(_nodes)

            if 'in'   in direction: _walk_coll('in',   self.in_sockets   )
            if 'side' in direction: _walk_coll('side', self.side_sockets )
            if 'out'  in direction: _walk_coll('out',  self.out_sockets  )
                
            if return_links: 
                return res_nodes,res_links
            return res_nodes
    
            
    class socket_collection_mixin(_mixin.socket_collection):
        def other_nodes(self, yield_links=False):
            ''' Yields other nodes and optional link that goes there '''

            if self.Direction in ('in','side'): other_attr = 'from_node'
            else:                               other_attr = 'to_node'

            for socket in self:
                for link in socket.links:
                    other_node = getattr(link,other_attr)
                    if yield_links: yield other_node, link
                    else:           yield other_node
                        

    # class link_mixin(_mixin.link):
    #     ...
