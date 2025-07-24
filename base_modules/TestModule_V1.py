from ..models.base_node      import socket, socket_collection,socket_group
from ..models.struct_module_types import mixin, item
from ..models.struct_module import module

class main(module):
    UID          = 'TestModule'
    Desc         = ''' '''
    Version      = '1.0'
    Deps         = []

    _loader_items_  : list
    _loader_mixins_ : list
        # If interdeps exist, it can be easier to append them instead of placing them inside the module

    class node_mixin(mixin.node):
        ''' Mixes into all node's base class, for hooking and base behavior changes '''

class new_socket(item.socket):
    #### IO Info  ####
    UID     = 'TestNode'
    Version = '1.0'
    Label   = 'TestNode'
    Desc    = '''  '''
    #### Socket Eval Info ####
    Value_Type       = str
    Value_Allow      = [str]
    Value_Default    = ''

    Disc_Cachable    : bool

    Default_ID       : str 
    Default_Label    : str #TODO: Merge with Label

    #TODO: Allow new fields to be read/written via IO

    # Call_Cache_Load  : bool = False
    # Call_Cache_Dump  : bool = False

    # def cache_dump(self,dir):...
    # def cache_load(self):    ...

class new_exec_node(item.node):
    ...

class new_meta_node(item.node):
    ''' Is a new node class, for execution and hooks 
    Note: inherits all node_mixins from all enabled modules'''
    UID     = 'TestNode'
    Version = '1.0'
    Label   = 'TestNode'
    Desc    = '''  '''

    Soft_Dependencies : list[tuple[str,str]] = []
        #Load if these modules, versions
    
    in_sockets = [new_socket,new_socket]

    test_value = 'Construction Worked!'

    in_sockets   = [socket_group.construct('set_a', Sockets=[new_socket]),
                    socket_group.construct('set_b', Sockets=[new_socket],   #TODO: allow default socket values via socket_group
                                        Set_ID='{nodeUID}_linked',
                                        Socket_Quantity_Min=1,
                                        Socket_Quantity_Max=10)]
    out_sockets  = [socket_group.construct('set_b',
                                        Sockets=[new_socket],
                                        Set_ID='{nodeUID}_linked')]
    side_sockets = []
        #Propery Input values, tracked as sockets for allowence of references

    def compile(self,exec_graph):

        #TODO: Determine actual flow, this is a sketch!
        #Actual flow will use contextVar access more inside the instance

        with self.compile_context():        #Add self to context for 
            self.compile_all_inputs()       #Compiles inputs, sets self hashes
            
            inst=new_exec_node()
            inst.default_sockets()
            inst.in_sockets['input_1'].set_pointer(self.in_sockets[0].exec_ref )
            inst.in_sockets['input_2'].set_pointer(self.in_sockets[1:].exec_ref)
            # inst.in_sockets.groups['set_b'].set_pointer_from_meta(*self.in_sockets[1:])

            self.out_sockets.groups['set_b'].set_pointer_from_exec(*inst.out_sockets.groups['set_b'])
                #Sockets should be ordered. Grab temp references from in sockets


            inst.set_hashes()
            exec_graph.append(inst)

main._loader_items_ = [new_socket, new_exec_node, new_meta_node]