from ..models.base_node import meta_graph

from ..models.base_node import node       as _node_base
from ..models.base_node import graph      as _graph_base
from ..models.base_node import meta_graph as _meta_graph_base

def test_graph_construction():
    m_graph = meta_graph()
    graph   = m_graph.graphs.new('Primary_Graph','Primary_Graph', module_iten = {
        'TestModule'     : '2.0',
        'Core_Execution' : '2.0',
        })
        # Assume version newest 
        # Use symbol of ^ for newest
        # On export the newest does get converted to its static version
    m_graph._Set_As_Active_Construction(graph)
        #Should be constructing the structure.
        #Consider hooks on collections to parent via context
    new_subgraph = graph.subgraphs.new('Test','Test')
    new_node     = new_subgraph.nodes.new(type='TestNode',key='TestNode',label='TestNode',default_sockets=True)
        #Could also import from module, instance and append to collection
        #This does require that the type be in the enabled collections
    
    #Testing Mixins
    # raise Exception(_node_base.__bases__)
    assert not _meta_graph_base.test_value
    assert not _node_base.test_value       
    assert not _graph_base.test_value

    # #Testing items
    # assert m_graph.test_value
    # assert graph.test_value
    assert new_node.test_value
    assert new_node.in_sockets[0].test_value