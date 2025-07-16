from .base_node import base_socket, base_node, base_node_set
from typing import Self, Any
from .struct_file_io import flat_ref, flat_col

class exec_socket(base_socket):
    node   : flat_ref['exec_node', base_node]

class exec_node(base_node):
    #### Constructed Values ####
    Node_Id : str
    Version : str

    #### Instance Attr ####
    meta_uuid:str

    in_value_hash   : str #Hash IDs stored on the socket
    in_context_hash : str 

    @classmethod
    def create(cls, *args,**kwargs)->list[Self]:
        return cls.create_indv(*args,**kwargs)

    @classmethod
    def create_indv(cls,*args,**kwargs)->Self:
        return cls(*args,**kwargs)
    
    def __init__(self):
        self.context = self.context(self)
        with self.context.register():
            self.in_sockets  = self.in_sockets()
            self.out_sockets = self.out_sockets()
    
    def execute(self):
        ''' Run the exec node! '''
        raise Exception(f"This exec_nodes Node's ({self.Type_Id} : {self.Version}) execution has not been defined yet!")

# class exec_node_set(base_node_set):
#     ''' exec node sets do not seem usefull at the moment, but as the bases are the same it should be somewhats straightforward to impliment later'''
#     ...