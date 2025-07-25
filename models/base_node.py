''' 
Base graph > node > socket structure, deep copied and constructed with loader
Graph Execution logic in a module constructed onto this set
'''

from .struct_file_io         import BaseModel, defered_archtype,flat_bin,flat_col,flat_ref 
from .struct_context         import context
from .struct_collection_base import item_base, collection_base, collection_typed_base
from .struct_construction    import ConstrBase, Bases, Constructed

from types                   import FunctionType
from typing                  import Any,Self
from collections             import defaultdict

class node_archtype(defered_archtype):...
class socket_archtype(defered_archtype):...
# class subgraph_archtype(defered_archtype):...
# class graph_archtype(defered_archtype):...


class pointer_socket(BaseModel,ConstrBase):
    ''' Pointer to a socket via node.{dir}_socket.[socket_id] '''
    _constr_bases_key_ = 'pointer_socket'
    _constr_call_post_ = ['__io_setup__']

    node       : flat_ref[node_archtype]
    socket_id  : str|int
    socket_dir : str = 'out'

    def __init__(self):
        self.context = self.context(self)
    
    context = context.construct(include=['meta_graph','root_graph','sub_graph','node','socket_coll','socket_group','socket'])
    def _context_walk_(self):...

    @classmethod
    def from_socket(cls, socket):
        inst = cls()
        sc = socket.context
        inst.node       = sc.node
        inst.socket_dir = sc.collection.direction
        inst.socket_id  = socket.id 

    @property
    def socket(self):
        if self.socket_dir == 'out':
            return self.node.out_sockets[self.socket_id]
        elif self.socket_dir == 'in':
            return self.node.in_sockets[self.socket_id]
        elif self.socket_dir == 'side':
            return self.node.side_sockets[self.socket_id]
        raise Exception(f'Socket direction "{self.socket_dir}" is not found!')


class socket(BaseModel,item_base,ConstrBase):
    _constr_bases_key_ = 'socket'
    _constr_call_post_ = ['__io_setup__']
    ''' 
    Module constructed socket type, 
    Interactions/rules are defined on socket_group
    Responcible for writing & retrieving specific data types 
    '''

    #### Constructed Values, Not Stored ####
    Value_Type  : Any       = Any
    Value_Allow : list[Any] = [Any]
        # Fallback values from socket_group.

    Disc_Cachable   : bool = True
        # If this socket can be cached to disc or not
        # If false, invalidates disc_cachable on exec_node

    Call_Cache_Dump : bool = False
    Call_Cache_Load : bool = False
        # If true, calls dump and load on execution

    Default_ID      : str
    Default_Label   : str


    #### Constructed Methods ####
    def cache_dump(self,dir):
        ''' Dump cache infor to location w/a, set disc_loc and disc_cached for cache_load'''
    def cache_load(self):
        ''' Load cache from disc_loc, set to self.value '''


    ####  Inst Props, Stored ####
    _io_whitelist_ = ['id', 'label', 'group_id', 'value', 'disc_cached', 'disc_location', 'out_links']

    id       : str
    label    : str

    group_id : str 
    group_set_id : str
        #IDs for socket_group container & subset

    value    : Any
    
    disc_cached   : bool = False
    disc_location : str
        #Hooks will convert spaces from & to `<SpaceID>/...` Format

    out_links : list[pointer_socket]


    #### Internal Methods ####

    def __init__(self):
        self.out_links = []
        self.context = self.context(self)

    context = context.construct(include=['meta_graph','root_graph','sub_graph','node','socket_coll','socket_group'],as_name='socket')
    def _context_walk_(self):
        with self.context.register():        
            for sl in self.out_links:
                sl.context._Get()


class socket_group[SocketType=socket](ConstrBase):
    _constr_bases_key_ = 'socket_group'
    _constr_call_post_ = ['__io_setup__']
 
    ''' 
    Constructed Class for methods to allow sockets 0+ to interact
    Defines UI interaction & validation of a socket type
    '''
    #TODO: Consider having sockets being quiried subset of parent socket_collection

    #### Constructed Data ####

    Group_ID : str
    Set_ID   : str|None = None
        #Used in events, runtime context-formatted string
    
    Value_Allow  : list[Any]|None = None 
        #If none, defers to per socket type allowed types

    Socket_Set_Base     : list[socket]
    Socket_Quantity_Min : int = 1
    Socket_Quantity_Max : int = 1

    Socket_Mutable      : bool        
    Socket_Mutatle_Pool : list[socket]

    def Socket_Label_Generator(self,socket:socket):
        return socket.Default_Label
    def Socket_ID_Generator(self,socket:socket):
        ''' Verify ID is Unique before attaching '''
        uid_base = socket.Default_ID
        uid = uid_base
        i = 0
        while uid in self.parent_col.sockets.keys():
            i=+1
            uid = uid_base + '.' + str(i).zfill(3)
        return uid

    #### Base Methods ####
    @classmethod
    def construct(cls,
                  group_id:str,
                  *,
                  Sockets:list[socket],
                  **kwargs
                  ):
        if not isinstance(Sockets,(list,tuple,set)):
            Sockets = list(Sockets)
        kwargs['Group_ID']        = group_id
        kwargs['Socket_Set_Base'] = Sockets
        return type(f'S_GROUP_{group_id}',(cls,),kwargs)


    def __init__(self,parent_col):
        self.context = self.context(self)
        self.parent_col = parent_col

    def default_sockets(self):
        for i in range(self.Socket_Quantity_Min):
            self.create_set(i)

    def create_set(self,set_id:int=0):
        while set_id in self.socket_sets.keys():
            set_id += 1

        ret = []
        for socket_base in self.Socket_Set_Base:
            inst = socket_base()
            inst.label = self.Socket_Label_Generator(inst)
            inst.id    = self.Socket_ID_Generator(inst)
            inst.group_set_id = set_id
            self[inst.id] = inst
            ret.append(inst)

        return ret



    @property
    def sockets(self):
        ret = {}
        for k,v in self.parent_col.sockets.items():
            if v.group_id == self.Group_ID:
                ret[k]=v
        return ret
    
    @property
    def socket_sets(self)->dict[dict[str,socket]]:
        ret = {}
        for k,v in self.sockets.items():
            if (_k:=v.group_set_id) not in ret.keys():
                ret[_k] = {}
            ret[_k][k] = v
        return ret

    def __getitem__(self,key)->SocketType:
        return self.sockets[key]

    def __setitem__(self,key,socket:SocketType):
        socket.group_id = self.Group_ID
        if socket not in self.parent_col.sockets.values():
            self.parent_col.sockets[key] = socket

    context = context.construct(include=['meta_graph','root_graph','sub_graph','node','socket_coll',],as_name='socket_group')
    def _context_walk_(self):
        with self.context.register():        
            for s in self.sockets.values():
                s._context_walk_()


class socket_collection(BaseModel,collection_typed_base,ConstrBase):
    ''' Accessor of sockets and socket_groups '''
    _constr_bases_key_ = 'socket_collection'
    _constr_call_post_ = ['__io_setup__']

    _io_bin_name_      = 'socket'
    _io_dict_like_     = True
    _io_blacklist_     = ['Groups','groups','data']
        #Data accessed by IO through dict-like interface.

    #### Constructed Values ####
    Groups    : list[socket_group]
    Direction : str

    @property
    def Bases(self)->dict[str,Any]:
        return self.context.root_graph.mod_col.items_by_attr('_io_bin_name_','socket')

    @classmethod
    def construct(cls,name:str,/,Groups:list[socket_group]|list[socket], Direction:str, **kwargs):
        if not isinstance(Groups,(list,tuple,set)):
            Groups = [Groups]
        if issubclass(Groups[0],socket):
            _g = socket_group.construct('main',Sockets=Groups)
            Groups = [_g]
        elif issubclass(Groups[0],cls):
            raise Exception('COLLECTION HAS BEEN PASSED INTO COLLECTION CONSTRUCTION')

        kwargs['Groups'] = Groups
        kwargs['Direction'] = Direction
        return type(name,(cls,),kwargs)

    def __init__(self):
        self.context = self.context(self)
        self.groups  = {}
        for v in self.Groups:
            assert issubclass(v,socket_group)
            self.groups[v.Group_ID] = v(self)

    context = context.construct(include=['meta_graph','root_graph','sub_graph','node'],as_name='socket_coll')
    def _context_walk_(self):
        with self.context.register():
            for sg in self.groups.values():
                sg._context_walk_()

    #### Instance Values ####
    groups  : dict[socket_group]
    data    : dict[socket]

    def __init__(self):
        self.context = self.context(self)
        self.data = {}
        self.groups  = {}
        for v in self.Groups:
            self.groups[v.Group_ID] = v(self)

    def default_sockets(self):
        for k,v in self.groups.items():
            v.default_sockets()

class node(BaseModel,ConstrBase):
    _constr_bases_key_ = 'node'
    _constr_call_post_ = ['__io_setup__']
    _io_bin_name_ = 'g_node'

    in_sockets   : socket_collection
    out_sockets  : socket_collection
    side_sockets : socket_collection

    def __init_subclass__(cls):
        if isinstance(cls.in_sockets,   (list,tuple,set)): 
            cls.in_sockets   = socket_collection.construct('in_sockets',   Direction='in',   Groups=cls.in_sockets)
            print(cls.in_sockets)
        if isinstance(cls.out_sockets,  (list,tuple,set)): 
            cls.out_sockets  = socket_collection.construct('out_sockets',  Direction='out',  Groups=cls.out_sockets)
        if isinstance(cls.side_sockets, (list,tuple,set)): 
            cls.side_sockets = socket_collection.construct('side_sockets', Direction='side', Groups=cls.side_sockets)
        assert issubclass(cls.in_sockets,   socket_collection)
        assert issubclass(cls.out_sockets,  socket_collection)
        assert issubclass(cls.side_sockets, socket_collection)

    context = context.construct(include=['meta_graph','root_graph','sub_graph'],as_name='node')
    def _context_walk_(self):
        with self.context.register():
            self.in_sockets._context_walk_()
            self.out_sockets._context_walk_()
            self.side_sockets._context_walk_()

    def __init__(self,/,*,default_sockets:bool = False):
        self.context = self.context(self)
        self.in_sockets  = self.in_sockets()
        self.out_sockets = self.out_sockets()
        self.side_sockets = self.side_sockets()
        if default_sockets:
            self.default_sockets()

    def default_sockets(self):
        self.in_sockets.default_sockets()
        self.out_sockets.default_sockets()
        self.side_sockets.default_sockets()


class node_collection(BaseModel, collection_typed_base, ConstrBase):
    _constr_bases_key_ = 'node_collection'
    _constr_call_post_ = ['__io_setup__']
    _io_bin_name_  = 'node'
    _io_dict_like_ = True
    _io_blacklist_ = ['data']

    @property
    def Bases(self)->dict[str,Any]:
        return self.context.root_graph.mod_col.items_by_attr('_io_bin_name_','g_node')

    data : list[node_archtype]

    context = context.construct(include=['meta_graph','root_graph','sub_graph'])
    def _context_walk_(self):
        with self.context.register():
            for v in self.data.values:
                v._context_walk_()

    def __init__(self):
        self.context = self.context(self)
        self.data = []


class subgraph(BaseModel, item_base, ConstrBase):
    _constr_bases_key_ = 'subgraph'
    _constr_call_post_ = ['__io_setup__']
    _io_bin_name_ = 'subgraph'
    nodes : flat_col[node_collection]

    context = context.construct(include=['meta_graph','root_graph'],as_name = 'sub_graph')
    def _context_walk_(self):
        with self.context.register():
            self.nodes._context_walk_()

    def __init__(self,):
        self.context = self.context(self)
        self.nodes = node_collection()


class subgraph_collection[SubgraphType=subgraph](BaseModel, collection_base, ConstrBase):
    _constr_bases_key_ = 'subgraph_collection'
    _constr_call_post_ = ['__io_setup__']
    _io_bin_name_ = 'subgraph'
    _io_dict_like_ = True
    _io_blacklist_ = ['data']
    Base = subgraph
    data : dict[subgraph]

    def __init__(self):
        self.context = self.context(self)
        self.data = []

    context = context.construct(include=['meta_graph','root_graph','sub_graph'])
    def _context_walk_(self):
        with self.context.register():
            for v in self.data:
                v._context_walk_()
    
from .struct_module_collections import (local_module_collection, 
                                        Global_Module_Pool)         #Singleton inst of global_module_collection

class graph(BaseModel, ConstrBase):
    _constr_call_post_ = ['__io_setup__']
    _constr_bases_key_ = 'graph'

    _io_blacklist_ = ['active','g_module_col']

    _nodes      : flat_bin[node]
    _subgraphs  : flat_bin[subgraph]
    subgraphs : flat_col[subgraph_collection]

    active      : bool = False

    Global_Module_Pool = Global_Module_Pool
    
    module_col   : local_module_collection 
    

    label : str

    context = context.construct(include = ['meta_graph'],as_name = 'root_graph')
    def _context_walk_(self):
        with self.context.register():
            self.nodes._context_walk_()

    def __init__(self,modules_iten:dict=None):
        self.context   = self.context(self)
        self.module_col = local_module_collection(modules_iten=modules_iten)
        self.subgraphs  = subgraph_collection()


class graph_collection(BaseModel, collection_base, ConstrBase):
    _constr_bases_key_ = 'graph_collection'
    _constr_call_post_ = ['__io_setup__']
    _io_bin_name_ = 'graph'
    _io_dict_like_ = True
    _io_blacklist_ = ['data']
    Base = graph
    data : dict[subgraph]

    context = context.construct(include=['meta_graph'])
    def _context_walk_(self):
        with self.context.register():
            for v in self.data:
                v._context_walk_()


class meta_graph(BaseModel, ConstrBase):
    ''' Should have a single instance, holds graphs, sets active. If more than one instance the latest active's modules are used. '''
    ''' Current design limitation of structure for flexibility to instnace manually in user modules. '''
    _constr_call_post_ = ['__io_setup__']
    _constr_bases_key_ = 'metagraph'
    Global_Module_Pool = Global_Module_Pool

    _graphs  : flat_bin[graph]
    graphs   : flat_col[graph_collection]

    context = context.construct(as_name='meta_graph')
    def _context_walk_(self):
        with self.context.register():
            self.graph._context_walk_()

    def _Set_As_Active_Construction(self,graph_inst:graph):
        ''' Construct in place all types using modules list '''
        ''' This does limit the active graph count to 1, inactive graphs will have to disable hooks '''

        module_col = graph_inst.module_col
        assert graph_inst.active
        
        mixins = defaultdict(dict)
        for x in module_col.mixins:
            key = getattr(x,'_constr_bases_key_','_uncatagorized')
            mixins[key] = x

        with Bases.set(mixins):
            pointer_socket.Construct(recur=False)
            socket.Construct(recur=False)
            socket_group.Construct(recur=False)
            socket_collection.Construct(recur=False)
            node.Construct(recur=False)
            node_collection.Construct(recur=False)
            subgraph.Construct(recur=False)
            subgraph_collection.Construct(recur=False)
            graph.Construct(recur=False)
            graph_collection.Construct(recur=False)
            self.__class__.Construct(recur=False)


def _Load_Types():
    ''' Fullfill object types post loader, pre-import'''
    items  = defaultdict(dict)

    for x in Global_Module_Pool.items:
        key = getattr(x,'_constr_bases_key_','_uncatagorized')
        items[key] = x

    node_archtype.types   = items['node']
    socket_archtype.types = items['socket']

def general_test():
    print(pointer_socket)
    print(socket)
    print(socket_group)
    print(socket_collection)
    print(node)
    print(node_collection)
    print(subgraph)
    print(subgraph_collection)
    print(graph)
    print(graph_collection)
    print(meta_graph)
