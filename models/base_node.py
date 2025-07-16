from .struct_file_io import BaseModel,flat_col,flat_ref
from typing import Any, Self
from types  import FunctionType
from .struct_context import context

class _unset:...
#Following are primary for meta_nodes interactions, but can be usefull in exec_nodes

class base_socket_refs(BaseModel):
    node   : flat_ref['exec_node', exec_node]
    socket : str

    context = context.construct(include=['root_graph','sub_graph','node','socket_coll','socket_group','socket'])


class base_socket(BaseModel):
    ''' Socket Type, will need some work in setting fields method '''
    #### Constructed Props, Not Stored ####
    Type    : str 
    Color   : list[float,float,float,float]

    #### Instance Props, Stored ####
    __file_io_attrs__ = ['group_id', 'out_links', 'disc_cached', 'disc_location','value']
    group_id      : str
    
    out_links     : list[base_socket_refs]
    value         : Any

    disc_cached   : bool = False
    disc_location : str
        #TODO DEFER: When a disc location has <...> it refers to a space and needs to be post processed on load

    def __init__(self):
        self.context = self.context(self)
        self.out_links = []

    def cache_dump(self, dir):
        ''' dump cache info to location w/a. Change self to ref location '''
        ''' When disc cached via space, post processed via external to make space relative '''

    def cache_load(self):
        ''' Optionally load info from location w/a '''
        ''' disc_location is processed on load to be absolute in current space '''

    context = context.construct(include=['root_graph','sub_graph','node','socket_coll','socket_group'],name_as='socket')
    def _context_walk_(self):
        with self.context.register():        
            for s in self.out_links:
                s.context.register()

class struct_socket_group[SocketType]:
    ''' Constructed socket group for ways to interpret sockets '''
    #### Class Data ####
    Group_ID : str   #Group matching ID, added to created sockets
    Set_ID                 : str|None = None 
    
    Value_Type  : Any|base_socket|list[base_socket]
    Value_Allow : list[Any]|FunctionType

    Socket_Quanity_Min     : int = 1
    Socket_Quanity_Max     : int = 1

    Socket_Name_Generator  : FunctionType
    Socket_ID_Generator    : FunctionType


    @classmethod
    def construct(cls,group_id,*,types:list[Any]|Any,set_id=None,**kwargs):
        if not isinstance(types,(list,tuple,set)):
            types = [types]
        kwargs['Group_ID']   = group_id
        kwargs['Value_Type'] = types
        kwargs['Set_ID']     = set_id
        return type(f'S_GROUP_{group_id}',(cls,),kwargs)
        
    context = context.construct(include=['root_graph','sub_graph','node','socket_coll'],name_as='socket_group')
    def _context_walk_(self):
        with self.context.register():
            for s in self.sockets.values():
                s._context_walk_()

    #### Inst data ####
    sockets : dict[base_socket]

    def __init__(self):
        self.context = self.context(self)
        self.sockets = {}
        with self.context.register():
            #TODO: Create Number of sockets as required
            ...

    def __get_item__(self,key)->SocketType:
        return self.sockets[key]
    def __set_item__(self,key,socket:SocketType):
        socket.group_id = self.Group_ID
        self.sockets[key] = socket
    

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

        with self.context.register():
            for group in self.CollectionBases:
                _g = group()
                self.groups[_g.Group_ID] = _g

    def _import_(self,data:dict):
        # dict is of socket_like types, interpret via group_id
        ...

    def _export_(self)->dict:
        ...

    context = context.construct(include=['root_graph','sub_graph','node'],name_as='socket_coll')
    def _context_walk_(self):
        with self.context.register():
            for sg in self.groups:
                sg._context_walk_()

class base_node(BaseModel):
    #TODO: Bring over other operating constants

    Node_Set_Components : list|None = None
    
    node_set_id       : str|None  = None
    node_set_members  : list|None = None

    in_sockets   : struct_socket_collection|list[struct_socket_group]
    out_sockets  : struct_socket_collection|list[struct_socket_group]
    side_sockets : struct_socket_collection|list[struct_socket_group]   #Properties
    
    #### Structural Functions ####
    def __init_subclass__(cls):
        if isinstance(cls.in_sockets,list):
            cls.in_sockets  = struct_socket_collection.construct('in_sockets',Direction='in',Groups=cls.in_sockets)
        if isinstance(cls.out_sockets,list):
            cls.out_sockets = struct_socket_collection.construct('out_sockets',Direction='out',Groups=cls.out_sockets)
        if isinstance(cls.side_sockets,list):
            cls.side_sockets = struct_socket_collection.construct('side_sockets',Direction='side',Groups=cls.side_sockets)
        assert issubclass(cls.in_sockets,struct_socket_collection)
        assert issubclass(cls.out_sockets,struct_socket_collection)
        super().__init_subclass__(cls)

    context = context.construct(include=['root_graph','sub_graph'],name_as='node')
    def _context_walk_(self):
        with self.context.register():
            self.in_sockets._context_walk_()
            self.out_sockets._context_walk_()
    
    def __init__(self):
        self.context = self.context(self)
        with self.context.register():
            self.in_sockets  = self.in_sockets()
            self.out_sockets = self.out_sockets()

    #### Default Operation Functions ####
    
    #### Class IO ####
    @classmethod
    def create(cls, *args,**kwargs)->list[Self]:
        return cls.create_indv(*args,**kwargs)

    @classmethod
    def create_indv(cls,*args,**kwargs)->Self:
        return cls(*args,**kwargs)

    #### Constructed Operation Functions ####
    def execute(self):
        raise Exception(f"This Base_nodes Node's ({self.UID} : {self.Version}) execution has not been defined yet!")

class base_node_set(base_node):
    #### Auto Constructed Attributes ####
    Node_Set_Components : list[base_node]

    #### Dev Constructed Attributes ####
    Node_Set_Min : 1
    Node_Set_Def : 1
    Node_Set_Max : 1
        # Add num of Default on Create, 
        # allow Min without removing group, 
        # dont allow adding to group past max 


    #### Construction ####
    @classmethod
    def construct(cls, group_name:str):
        ''' Construct an exec_node class variant to mixin to classes '''
        return type(group_name,(cls,),{
            'Node_Set_Components' : [],
        })
    
    #### Structural Functions ####
    @classmethod
    def __init_subclass__(cls):
        cls.Node_Set_Components.append(cls)
        return super().__init_subclass__()

    #### Class IO ####
    @classmethod
    def create_set(cls)->list[base_node]:
        ''' Generate New Set with Def num of each component ''' 
        #node_set_members = [] 
        #inst.node_set_id
        #inst.node_set_members = node_set_members 
        #TODO
        ...
    
    @classmethod
    def create()->list[base_node]:
        ''' Create Indvidual respencing each min/max of selected set '''
        ...


class _test:
    #TODO: Move to another file
    global test_socket
    class test_socket(base_socket):
        ...

    global test
    class test(base_node):
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
    

    zone_a = base_node_set.construct('Node_Set')
    class test_zone_in(zone_a):
        in_sockets  = [struct_socket_group.construct('a',types=[test_socket])          ]
        out_sockets = [struct_socket_group.construct('a',set_id ='{set_group_uid}_set_a', types=[Any]) ]

    class test_zone_out(zone_a):
        in_sockets  = [struct_socket_group.construct('a',set_id ='{set_group_uid}_set_a', types=[Any]) ]
        out_sockets = [struct_socket_group.construct('a',types=[test_socket])          ]
    
    portal = base_node_set.construct('Node_Set')
    class test_portal_in(portal):
        in_sockets   = [struct_socket_group.construct('a',set_id='{set_group_uid}_set_a', types=[test_socket])           ]
    class test_portal_out(portal):
        out_sockets  = [struct_socket_group.construct('a',set_id='{set_group_uid}_set_a', types=[test_socket])           ]

    subgraph_int_reps = base_node_set.construct('Node_Set')
    class test_graph_in(subgraph_int_reps):
        in_sockets   = [struct_socket_group.construct('a',set_id='{sub_graph.uuid}_in',  types=[Any])   ]
    class test_graph_out(subgraph_int_reps):
        out_sockets  = [struct_socket_group.construct('a',set_id='{sub_graph.uuid}_out', types=[Any])   ]
        
    class subgraph_rep(base_node):
        graph_ref    : flat_ref['subgraph'] = _unset #type:ignore
        in_sockets   = [struct_socket_group.construct('a',set_id='{sub_graph.uuid}_in',  types=[Any]) ]
        out_sockets  = [struct_socket_group.construct('a',set_id='{sub_graph.uuid}_out', types=[Any]) ]
        
        @property
        def graph_id(self):
            ''' Defered to property/value in global_set_id set formation '''
            if self.graph_ref is not _unset:
                return self.graph_ref.instance_id
            else:
                return _unset