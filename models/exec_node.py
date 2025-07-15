from .struct_file_io import BaseModel,flat_col,flat_ref
from typing import Any, Self
from types  import FunctionType


class _unset:...
#Following are primary for meta_nodes interactions, but can be usefull in exec_nodes

class exec_socket_refs(BaseModel):
    node   : flat_ref['exec_node', exec_node]
    socket : str

class exec_socket(BaseModel):
    ''' Socket Type, will need some work in setting fields method '''
    group_id      : str
    
    out_links     : list[exec_socket_refs]

    disc_cached   : bool = False
    disc_location : str             
        #TODO DEFER: When a disc location has <...> it refers to a space and needs to be post processed on load

    value         : Any

    def __init__(self):
        self.out_links = []

    def cache_dump(self, dir):
        ''' dump cache info to location w/a. Change self to ref location '''
        ''' When disc cached via space, post processed via external to make space relative '''

    def cache_load(self):
        ''' Optionally load info from location w/a '''
        ''' disc_location is processed on load to be absolute in current space '''

class struct_socket_group[SocketType]:
    ''' Constructed socket group for ways to interpret sockets '''
    #### Class Data ####
    UID : str   #Group matching ID, added to created sockets
    
    Value_Type  : Any|exec_socket|list[exec_socket]
    Value_Allow : list[Any]|FunctionType

    Socket_Quanity_Min     : int = 1
    Socket_Quanity_Max     : int = 1

    Socket_Name_Generator  : FunctionType
    Socket_ID_Generator    : FunctionType

    @classmethod
    def construct(cls,name,/,**kwargs):
        return type(f'S_GROUP_{name}',(cls,),kwargs)
        

    #### Inst data ####
    sockets : dict[exec_socket]

    def __init__(self):
        self.sockets = {}


class struct_socket_collection():
    ''' Constructed collection of socket groups'''
    #### Constructed Values ####
    CollectionBases : list[struct_socket_group]
    Direction       : str   #In, SideIn, Out 
        #Direction this socket collection is pointing in

    @classmethod
    def construct(cls,name:str,/,groups:list[struct_socket_group], Direction:str, **kwargs):
        kwargs['CollectionBases'] = groups
        kwargs['Direction'] = Direction
        return type(name,(cls,),kwargs)
        
    #### Instance Values ####
    sockets : dict
    groups  : dict

    def __init__(self):
        self.sockets = {}
        self.groups  = {}
        for group in self.CollectionBases:
            _g = group(group_col = self)
            self.groups[_g.UID] = _g

    def _import_(self,data:dict):
        # dict is of socket_like types, interpret via group_id
        ...

    def _export_(self)->dict:
        ...


class exec_node(BaseModel):
    #TODO: Bring over other operating constants
    Node_Set_Components : list|None = None
    
    meta_node_uuid    : str
    meta_node_inst_id : str
    node_set_id       : str|None  = None
    node_set_members  : list|None = None

    in_sockets  : struct_socket_collection|list[struct_socket_group]
    out_sockets : struct_socket_collection|list[struct_socket_group]
    
    def __init_subclass__(cls):
        if isinstance(cls.in_sockets,list):
            cls.in_sockets = struct_socket_collection.construct('in_sockets',Direction='in',Groups=cls.in_sockets)
        if isinstance(cls.out_sockets,list):
            cls.out_sockets = struct_socket_collection.construct('out_sockets',Direction='out',Groups=cls.out_sockets)
        assert issubclass(cls.in_sockets,struct_socket_collection)
        assert issubclass(cls.out_sockets,struct_socket_collection)
        super().__init_subclass__(cls)

    def __init__(self):
        self.in_sockets  = self.in_sockets()
        self.out_sockets = self.out_sockets()

    @classmethod
    def create(cls, *args,**kwargs)->list[Self]:
        cls.create_indv(*args,**kwargs)

    @classmethod
    def create_indv(cls)->Self:
        ...

class exec_node_set(exec_node):
    Node_Set_Components : list[exec_node]

    @classmethod
    def __init_subclass__(cls):
        cls.Node_Set_Components.append(cls)
        return super().__init_subclass__()

    @classmethod
    def create(cls)->list[exec_node]:
        #Generate with 
        #node_set_members = [] 
        #inst.node_set_id
        #inst.node_set_members = node_set_members 
        #TODO
        ...

    @classmethod
    def construct(cls, group_name:str):
        ''' Construct an exec_node class variant to mixin '''
        return type(group_name,(cls,),{
            'Node_Set_Components' : [],
        })

class _test:
    #TODO: Move to another file
    global test_socket
    class test_socket(exec_socket):
        ...

    global test
    class test(exec_node):
        in_sockets = [
            struct_socket_group.construct('a',types=[test_socket]),
            struct_socket_group.construct('b',set_id='socket', types=[str])
            ]

        out_sockets = [
            struct_socket_group.construct('a',types=[test_socket]),
            struct_socket_group.construct('b',types=[str])
            ]

        def execute(self):
            self.in_sockets['a'].execute()
    

    zone_a = exec_node_set.construct('Node_Set')
    class test_zone_in(zone_a):
        in_sockets  = [struct_socket_group.construct('a',types=[test_socket])          ]
        out_sockets = [struct_socket_group.construct('a',set_id ='{set_group_uid}_set_a', types=[Any]) ]

    class test_zone_out(zone_a):
        in_sockets  = [struct_socket_group.construct('a',set_id ='{set_group_uid}_set_a', types=[Any]) ]
        out_sockets = [struct_socket_group.construct('a',types=[test_socket])          ]
    
    portal = exec_node_set.construct('Node_Set')
    class test_portal_in(portal):
        in_sockets   = [struct_socket_group.construct('a',set_id='{set_group_uid}_set_a', types=[test_socket])           ]
    class test_portal_out(portal):
        out_sockets  = [struct_socket_group.construct('a',set_id='{set_group_uid}_set_a', types=[test_socket])           ]

    subgraph_int_reps = exec_node_set.construct('Node_Set')
    class test_graph_in(subgraph_int_reps):
        in_sockets   = [struct_socket_group.construct('a',global_set_id='{graph_id}_in',  types=[Any])   ]
    class test_graph_out(subgraph_int_reps):
        out_sockets  = [struct_socket_group.construct('a',global_set_id='{graph_id}_out', types=[Any])   ]
        
    class subgraph_rep(exec_node):
        graph_ref    = flat_ref['subgraph'] = _unset
        in_sockets   = [struct_socket_group.construct('a',global_set_id='{graph_id}_in',  types=[Any]) ]
        out_sockets  = [struct_socket_group.construct('a',global_set_id='{graph_id}_out', types=[Any]) ]
        
        @property
        def graph_id(self):
            ''' Defered to property/value in global_set_id set formation '''
            if self.graph_ref is not _unset:
                return self.graph_ref.instance_id
            else:
                return _unset