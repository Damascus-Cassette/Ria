from ..base_node import meta_graph

def test_module_tests():
    m_graph = meta_graph()
    m_graph._run_tests()