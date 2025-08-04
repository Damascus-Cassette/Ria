from ..models.base_node      import socket, socket_collection,socket_group,graph
from ..models.struct_module_types import mixin, item
from ..models.struct_module_types import _mixin 

from ..models.struct_module import module
from ..models.struct_file_io import flat_ref

from typing import Any

class main(module):
    UID          = 'TestModule'
    Label        = 'TestModule'
    Desc         = ''' Testing if the factory/loader method works '''
    Version      = '1.0'
    
    Deps : list[tuple[str,str,str,str]] = [
        ('required','TestModule','=(1.0)','Failure_Message')
    ]

    _loader_items_  : list #= []
    _loader_mixins_ : list #= []
        # when direct dependencies exist (as nodes->sockets), it can be easier to append them instead of placing them inside the module

    #### Mixins ####
        # Mixes into base classes, affects all of specified type.

    class node_mixin(mixin.node):
        test_value = False
    class socket_mixin(mixin.socket):
        test_value = False
    class graph_mixin(_mixin.graph):
        test_value = False
    class metagraph_mixin(_mixin.meta_graph):
        test_value = False

class new_socket(item.socket):
    #### Automatic if subclass of main(Module) ####
    Module : module = main 

    #### IO Info  ####
    UID     = 'TestNode'
        # Must be unique to all enabled modules (but not versions of this module, as only one version can be loaded)
        # This used to load the socket from disc into this type from a global pool (also utilizing module.UID and module.version)
        # This is also the default Default_key in a collection. 
    Version = '1.0'
        # Version of the socket, used when validating a cache.
        # If the version is different from the cache, the cache is not used.
    Label   = 'TestNode'
        # User Facing label
        # This is also the default Default_Label in a collection.
    Desc    = '''  '''
        #User facing description, defaults to class Description
    
    Deps : list[tuple[str,str,str,str]]
        #Typically only used by nodes & modules.
        #On Items it allows enable_if_any|all statment modes.


    #### Socket Type Eval & Handling Info ####
    Value_Types             : list[Any]  = [str]
    Value_Allow             : list[Any]  = [str]  #Allows connection with, Default is [Any]     can also be socket types or typing.Self
    Value_Disallow          : list[Any]  = [None] #Disallows connection with using Value_Types, can also be socket types or typing.Self

    Value_Default           : str        = ''
    Value_Default_Copy      : bool #= True
    Value_Default_DeepCopy  : bool #= True

    Disc_Cachable    : bool
        #If the value can be cached to a disk, or is a python in memory only value
    Default_ID       : str
        #Default Key   in a collection. Run through a function to ensure it's unique
    Default_Label    : str
        #Default Label in a collection. Run through a function that could be changed to ensure it's unique

    Call_Cache_Load  : bool #= False
    Call_Cache_Dump  : bool #= False
    def cache_dump(self,dir): ...
    def cache_load(self):     ...

    #Test value:
    test_value      = True

# class new_exec_node(item.node):
#     test_value      = True

class new_meta_node(item.node):
    ''' Is a new node class, for execution and hooks 
    Note: inherits all node_mixins from all enabled modules'''
    UID     = 'TestNode'
    Version = '1.0'
    Label   = 'TestNode'
    Desc    = '''  '''
    Module  = main 

    Deps : list[tuple[str,str,str,str]] = [
        ('enable_if_any','TestModule','=(1.0)','Failure_Message')
    ]
        #Load if these modules, versions
    test_value      = True
    
    in_sockets = [new_socket,new_socket]

    test_value = 'Construction Worked!'

    in_sockets   = [socket_group.construct('set_a', Sockets=[new_socket]),
                    socket_group.construct('set_b', Sockets=[new_socket],   #TODO: allow default socket values via a socket_preset type?
                                        Set_ID='{node}_linked',             # Utilizing (context.__dict__|context.node.__dict__) to fullfill values.
                                        Socket_Quantity_Min=1,                  #This way you can determine pools of connected socket_groups, where sets (determined by Sockets=[]) are tied in count.
                                        Socket_Quantity_Max=10)]                #Such as a node using a 'subgraph : flat_ref[subgraph]' (flatref so it can be saved) using '{subgraph}_input' and '{subgraph}_output'
    
    out_sockets  = [socket_group.construct('set_b',
                                        Sockets=[new_socket],
                                        Set_ID='{node}_linked')]
    
    side_sockets = []

        #Propery Input values, tracked as sockets for allowence of references and an easier structure.

    # def compile(self,exec_graph):

    #     #TODO: Determine actual flow, this is a sketch!
    #     #Actual flow will use contextVar access more inside the instance

    #     with self.compile_context():        #Add self to context for 
    #         self.compile_all_inputs()       #Compiles inputs, sets self hashes
            
    #         inst=new_exec_node()
    #         inst.default_sockets()
    #         inst.in_sockets['input_1'].set_pointer(self.in_sockets[0].exec_ref )
    #         inst.in_sockets['input_2'].set_pointer(self.in_sockets[1:].exec_ref)
    #         # inst.in_sockets.groups['set_b'].set_pointer_from_meta(*self.in_sockets[1:])

    #         self.out_sockets.groups['set_b'].set_pointer_from_exec(*inst.out_sockets.groups['set_b'])
    #             #Sockets should be ordered. Grab temp references from in sockets


    #         inst.set_hashes()
    #         exec_graph.append(inst)

main._loader_items_ = [new_socket, new_meta_node]
    #item.Module = main is required when doing this method

