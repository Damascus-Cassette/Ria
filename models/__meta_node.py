from ._base_node import base_socket, base_node, base_node_set
from .struct_file_io import flat_col, flat_ref
from typing import Self, Any

class meta_socket(base_socket):
    node   : flat_ref['meta_node', base_node] #type:ignore

class meta_node(base_node):
    Node_Id : str
    Version : str

    @classmethod
    def create(cls, *args,**kwargs)->list[Self]:
        return cls.create_indv(*args,**kwargs)

    @classmethod
    def create_indv(cls,*args,**kwargs)->Self:
        return cls(*args,**kwargs)
    
    def execute(self):
        ''' Generate an exec_node and place into the exec node bin. Also determines self.UUID context to pass in. '''
        raise Exception(f"This meta_nodes Node's ({self.UID} : {self.Version}) execution has not been defined yet!")

class meta_node_set(base_node_set):
    ...