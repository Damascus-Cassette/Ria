from ..models.struct_module  import mixin, item
from ..models.base_node      import socket

UID          = 'TestModule'
Desc         = ''' '''
Version      = '1.0'
Dependencies = []
Soft_Dependencies = []

class node_mixin(mixin.node):
    ''' Mixes into all node's base class, for hooking and base behavior changes '''

class new_socket(item.socket):
    UID     = 'TestNode'
    Version = '1.0'
    Label   = 'TestNode'
    Desc    = '''  '''

class new_node(item.node):
    ''' Is a new node class, for execution and hooks 
    Note: inherits all node_mixins from all enabled modules'''
    UID     = 'TestNode'
    Version = '1.0'
    Label   = 'TestNode'
    Desc    = '''  '''

    Soft_Dependencies = []
        #Load if these modules, versions
    
    in_sockets = [new_socket,new_socket]

    test_value = 'Construction Worked!'

