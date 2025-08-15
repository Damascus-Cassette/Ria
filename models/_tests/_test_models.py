from ..base_node import meta_graph

# def test_module_inheritance():
#     from ...models.struct_collection_base import item_base
#     from ...models.struct_construction import ConstrBase
#     from ...models.struct_hook_base import Hookable
#     object
#     from typing import Generic
#     from ...base_modules.Monadish_Interface_1_1 import socket_group_mixin
    
#     class new(item_base,
#               ConstrBase,
#               Hookable,
#               socket_group_mixin):
#         ...



def test_module_tests():
    m_graph = meta_graph()
    m_graph._run_tests()