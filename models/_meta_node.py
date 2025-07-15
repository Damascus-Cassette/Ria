from ._exec_node import exec_node, exec_socket
from . import context

from pydantic import BaseModel
from typing import Any
from types import FunctionType


'''
Struct:
meta_node / 
    i/o_sockets : struct_meta_socket_cont
        .collections : dict[struct_meta_socket_coll]
        .sockets     : dict[meta_socket]

'''

class address(BaseModel):
    type : str
    uuid : str

    def other(self):
        #TODO
        #Retrieve with context
        ...
    

class meta_socket(BaseModel):
    ''' Generic type, not constructed.
        This enforces seperation of data and handling '''
    name    : str
    id      : str
    coll_id : str

    value       : Any|None

    class Config: fields = {
        'collections':{'ignore':True}
        }

    _connections : list[address]
    

class struct_meta_socket_type():
    ''' Manually Constructed interface for a grouping of meta_socket(s) 
        utilized through the struct_meta_socket_coll '''

    Type_ID : str 
    Color   : list[float,float,float,float]

    
class struct_meta_socket_coll():
    ''' Manually Constructed Container/interface for sockets, used in typing & socket contstruction. Bypassed in exporting '''

    #### Type Data      ####
    UID : str

    Value_Type       : Any|struct_meta_socket_type         
    Value_Allow      : list[Any]     #These value attrs could be references to a meta_types values, but that is not enforced

    Value_Conv       : FunctionType  
    Value_Cache_Dump : FunctionType  #Default is just pydantics dump
    Value_Cache_Load : FunctionType  

    Socket_Count_min : int = 1 
    Socket_Count_max : int = 1

    Socket_Name_Generator : FunctionType
    Socket_Id_Generator   : FunctionType 


    #### Instsance Data ####
    sockets : dict[meta_socket]


    #### Methods        ####
    def __init__(self, sockets:list[meta_socket]):
        self.sockets = {}
        for s in sockets:
            self.sockets[s.id] = s


class struct_meta_socket_cont(BaseModel):
    '''  '''

    collections : struct_meta_socket_coll

    class Config: fields = {
        'collections':{'ignore':True}
        }

    def __init__(self, *args, **kwargs):
        self.super().__init__(*args,**kwargs)
        self.sockets
        

    sockets : list[meta_socket]
    

class meta_node(BaseModel):
    ''' Constructed Exec_Node Generation '''
    sockets : struct_meta_socket_cont 


class meta_node_collection(BaseModel):
    ''' Automatically Constructed type used for representing lists of meta_nodes. Failure to import type results in automatic error type'''




class _example_meta_nodes:
    from ._exec_node import _exec_node_examples

    class example_meta_node(meta_node):
        ...
        
    __nodes__ = [example_meta_node]
    

