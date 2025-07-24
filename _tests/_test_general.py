from ..models.base_node import meta_graph

from ..models.base_node import node as _node_base
from ..models.base_node import graph as _graph_base
from ..models.base_node import meta_graph as _meta_graph_base

def test_graph_construction():
    m_graph = meta_graph()
    graph   = meta_graph.graphs.new('Primary_Graph','Primary_Graph', module_iten = {'TestModule':'1.0'})
    meta_graph._Set_As_Active_Construction(graph)
        #Should be constructing the structure.
        #Consider hooks on collections to parent via context??
    new_node = graph.nodes.new(type='TestNode',key='TestNode',label='TestNode',default_sockets=True)
        #Could also import from module, instance and append to collection
    
    #Testing Mixins
    assert not _meta_graph_base.test_value
    assert not _node_base.test_value       
    assert not _graph_base.test_value

    #Testing items
    assert new_node.test_value             
    assert graph.test_value