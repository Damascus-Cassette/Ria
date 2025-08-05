from ..base_node import meta_graph

def test_graph_construction():
    m_graph = meta_graph()

    graph = m_graph.graphs.new('Primary_Graph','Primary_Graph', module_iten = {'TestModule':'2.0'})
    m_graph._Set_As_Active_Construction(graph)
    for mod in graph.modules:
        for test in getattr(mod,'_test_module_',[]):
            new_subgraph = graph.subgraphs.new('Test','Test')
            test(graph,new_subgraph)
            graph.subgraphs.remove(new_subgraph)