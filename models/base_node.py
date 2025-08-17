''' 
Base graph > node > socket structure, deep copied and constructed with loader
Graph Execution logic in a module constructed onto this set
'''

from .struct_file_io         import BaseModel, defered_archtype,flat_bin,flat_col,flat_ref 
from .struct_context         import context
from .struct_collection_base import (item_base,
                                     collection_base,
                                     typed_collection_base,
                                    #  subcollection_base,
                                    #  typed_subcollection_base,
                                     context_prepped_subcollection_base,
                                     context_prepped_typed_subcollection_base,
                                     )
from .struct_construction    import ConstrBase, Bases, Constructed
from .struct_hook_base       import Hookable

from types                   import FunctionType
from typing                  import Any,Self,Callable
from collections             import defaultdict
from inspect                 import isclass

class node_archtype(defered_archtype):...
class socket_archtype(defered_archtype):...
# class subgraph_archtype(defered_archtype):...
# class graph_archtype(defered_archtype):...

from collections import OrderedDict

class link(BaseModel,item_base,ConstrBase,Hookable):
    ''' Pointer to a socket via node.{dir}_socket.[socket_id] '''
    _io_bin_name_       = 'link'
    _io_blacklist_      = ['name']

    _constr_bases_key_  = 'link'
    _constr_call_post_  = ['__io_setup__']
    _constr_join_dicts_ = ['_hooks']
    _constr_join_lists_ = ['_io_blacklist_','_io_whitelist_','_constr_call_post_']

    name : str
        #Collection Name, not written

    in_socket_node     : flat_ref[node_archtype] = None
    in_socket_dir      : str                     = 'in'
    in_socket_id       : str                     = None
        #Does NOT refer to socket.name (used by collection), as that is not recorded

    out_socket_node   : flat_ref[node_archtype] = None
    out_socket_dir    : str                     = 'out'
    out_socket_id     : str                     = None
        #Does NOT refer to socket.name (used by collection), as that is not recorded

    def __init__(self, out_socket=None, in_socket=None):
        self.context = self.context(self)
        self.out_socket = out_socket
        self.in_socket   = in_socket
    
    @property
    def out_socket(self):
        if (self.out_socket_node) and (self.out_socket_dir) and (self.out_socket_id is not None):
            return getattr(self.out_socket_node,self.out_socket_dir+'_sockets')[self.out_socket_id]
    @out_socket.setter
    def out_socket(self,socket):
        self.out_socket_node = socket.context.node
        self.out_socket_dir  = socket.context.socket_coll.Direction
        self.out_socket_id   = socket.id

    @property
    def in_socket(self):
        if (self.in_socket_node) and (self.in_socket_dir) and (self.in_socket_id is not None):
            return getattr(self.in_socket_node,self.in_socket_dir+'_sockets')[self.in_socket_id]
    @in_socket.setter
    def in_socket(self,socket):
        self.in_socket_node = socket.context.node
        self.in_socket_dir  = socket.context.socket_coll.Direction
        self.in_socket_id   = socket.id

    context = context.construct(include=['meta_graph','root_graph','subgraph','node','socket_coll','socket_group','socket'])
    def _context_walk_(self):...

class link_collection[SocketType = link](BaseModel,collection_base,ConstrBase,Hookable):
    ''' subgraph.links, filtered in the socket's view via a constructed function 
    May consider making typed if there is any good argument to do so.
    '''
    _io_bin_name_       = 'link'
    _io_dict_like_      = True
    _io_blacklist_      = ['Groups','groups','data']

    _constr_bases_key_  = 'socket_collection'
    _constr_call_post_  = ['__io_setup__']
    _constr_join_dicts_ = ['_hooks']
    _constr_join_lists_ = ['_io_blacklist_','_io_whitelist_','_constr_call_post_']

    context = context.construct(include=['meta_graph','root_graph','subgraph'], as_name='link_col')
    def _context_walk_(self):
        with self.context.register():
            for sg in self.groups.values():
                sg._context_walk_()
    
    Base = link

class link_subcollection(context_prepped_subcollection_base):
    #TODO: How does this work with FildIO?
    @property
    def _data(self):
        return self.parent.context.subgraph.links
    

class socket(BaseModel,item_base,ConstrBase,Hookable):
    ''' 
    Module constructed socket type, 
    Interactions/rules are defined on socket_group
    Responcible for writing & retrieving specific data types 
    '''
    _io_bin_name_       = 'socket'
    _io_whitelist_      = ['id', 'label', 'group_id', 'value', 'disc_cached', 'disc_location', 'links']
    _io_blacklist_      = ['incoming_links' ,'outgoing_links' ,'links']

    _constr_bases_key_  = 'socket'
    _constr_call_post_  = ['__io_setup__']
    _constr_join_dicts_ = ['_hooks']
    _constr_join_lists_ = ['_io_blacklist_','_io_whitelist_','_constr_call_post_']


    #### Constructed Values, Not Stored ####
    Default_ID      : str
    Default_Label   : str

    Link_Quantity_Min : int = 0
    Link_Quantity_Max : int = 1

    ####  Inst Props, Stored ####
    id       : str
    label    : str

    group_id : str 
    group_set_id : str
        #IDs for socket_group container & subset

    links  : context_prepped_subcollection_base #[link]
    # out_links  : subcollection_base[link]
    # in_links   : subcollection_base[link]

    context = context.construct(include=['meta_graph','root_graph','subgraph','node','socket_coll','socket_group'],as_name='socket')
    def _context_walk_(self):
        with self.context.register():        
            for sl in self.links:
                sl.context._Get()

    #### Internal Methods ####

    def __init__(self):
        self.context = self.context(self)

        self.incoming_links  = link_subcollection(self, lambda i,k,link :  link.in_socket  == self)
        #This socket stores/'owns' these links in the file format for portability
        self.outgoing_links  = link_subcollection(self, lambda i,k,link :  link.out_socket == self)
        
        self.links = link_subcollection(self, lambda i,k,link : link.out_socket == self or link.in_socket == self)
        #Refers to all links that mention self

    @property
    def dir(self):
        return self.context.socket_coll.Direction

# global _temp_sg_constr_index
# _temp_sg_constr_index = 0

class socket_group[SocketType=socket](item_base,ConstrBase,Hookable):
    ''' 
    Constructed Class for methods to allow sockets 0+ to interact
    Defines UI interaction & validation of a socket type
    '''
    _constr_bases_key_  = 'socket_group'
    _constr_call_post_  = ['__io_setup__']
    _constr_join_dicts_ = ['_hooks']
    _constr_join_lists_ = ['_io_blacklist_','_io_whitelist_','_constr_call_post_']
    
    #TODO: Consider having sockets being quiried subset of parent socket_collection

    #### Constructed Data ####

    Group_ID : str
    Set_ID   : str|None = None
        #Used in events, runtime context-formatted string
    
    Value_Allow  : list[Any]|None = None 
        #If none, defers to per socket type allowed types

    Socket_Set_Base          : list[socket]
    SocketGroup_Quantity_Min : int = 1
    SocketGroup_Quantity_Max : int = 1

    # Socket_Mutable      : bool        
    # Socket_Mutatle_Pool : list[socket]


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
        
        # global _temp_sg_constr_index 
        # _temp_sg_constr_index = _temp_sg_constr_index + 1
        # return type(f'S_GROUP_{_temp_sg_constr_index}_{group_id}',(cls,),kwargs)
        

    context = context.construct(include=['meta_graph','root_graph','subgraph','node','socket_coll',],as_name='socket_group')
    def _context_walk_(self):
        with self.context.register():        
            for s in self.sockets.values():
                s._context_walk_()


    #### Instance Methods ###
    
    def __init__(self,parent_col):
        self.context = self.context(self)
        self.parent_col = parent_col

    def Socket_Label_Generator(self,socket:socket):
        return getattr(socket,'Default_Label',socket.Label)
    
    def Socket_ID_Generator(self,socket:socket):
        ''' Verify ID is Unique before attaching '''
        uid_base = getattr(socket,'Default_ID',socket.UID)
        uid = uid_base
        i = 0
        while uid in self.parent_col.keys():
            i=+1
            uid = uid_base + '.' + str(i).zfill(3)
        return uid

    def default_sockets(self):
        for i in range(self.SocketGroup_Quantity_Min):
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
        for k,v in self.parent_col.items():
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

        # socket.group_id = self.Group_ID   #BUG: Was causing sockets to see themselves in the wrong group. 
        socket.group_id = self.key

        if socket not in self.parent_col.values():
            self.parent_col[key] = socket

class socket_group_collection(collection_base,ConstrBase,Hookable):
    ''' Shoudl be non-writable. Reconstructed on load. Accessor like an ordered dict '''
    Base = socket_group


    #BUG HERE. Not ensuring unique keys.

class socket_collection(BaseModel,typed_collection_base,ConstrBase,Hookable):
    ''' Accessor of sockets and socket_groups '''
    _io_bin_name_       = 'socket'
    _io_dict_like_      = True
    _io_blacklist_      = ['Groups','groups','data']

    _constr_bases_key_  = 'socket_collection'
    _constr_call_post_  = ['__io_setup__']
    _constr_join_dicts_ = ['_hooks']
    _constr_join_lists_ = ['_io_blacklist_','_io_whitelist_','_constr_call_post_']

    context = context.construct(include=['meta_graph','root_graph','subgraph','node'],as_name='socket_coll')
    def _context_walk_(self):
        with self.context.register():
            for sg in self.groups.values():
                sg._context_walk_()


    #### Class Methods ####

    @classmethod
    def construct_if_not(cls,name:str,/,Groups:list[socket_group]|list[socket], Direction:str, **kwargs):
        if isclass(Groups):
            if issubclass(Groups,cls):
                return Groups
        return cls.construct(name,Groups,Direction,**kwargs)

    @classmethod
    def construct(cls,name:str,/,Groups:list[socket_group]|list[socket], Direction:str, **kwargs):

        if not isinstance(Groups,(list,tuple,set)):
            Groups = [Groups]
        if len(Groups):
            if issubclass(Groups[0],socket):
                _g = socket_group.construct('main',Sockets=Groups)
                Groups = [_g]
            elif issubclass(Groups[0],cls):
                raise Exception('COLLECTION HAS BEEN PASSED INTO COLLECTION CONSTRUCTION')

        kwargs['Groups'] = Groups
        kwargs['Direction'] = Direction
        return type(name,(cls,),kwargs)


    #### Constructed Values ####
    Groups    : list[socket_group]
    Direction : str


    #### Instance Values ####
    # groups  : dict[socket_group]
    groups  : socket_group_collection
    data    : list[socket]
        #TODO: CONVERT TO COLLECTION

    def __init__(self):
        self.context = self.context(self)
        self._data   = OrderedDict()
        self.groups  = socket_group_collection()
        for v in self.Groups:
            self.groups[v.Group_ID] = v(self)

    def default_sockets(self):
        for k,v in self.groups.items():
            v.default_sockets()

    @property
    def Bases(self)->dict[str,Any]:
        return self.context.root_graph.module_col.items_by_attr('_io_bin_name_','socket')


class node(BaseModel,ConstrBase,Hookable):
    ''' Base Node type, inherited into actionable forms '''
    _io_bin_name_       = 'g_node'

    _constr_bases_key_  = 'node'
    _constr_call_post_  = ['__io_setup__']
    _constr_join_dicts_ = ['_hooks']
    _constr_join_lists_ = ['_io_blacklist_','_io_whitelist_','_constr_call_post_']

    _links       : flat_bin[link]

    in_sockets   : socket_collection #Consider mandating this structure def as capital
    out_sockets  : socket_collection #And inst as lowercase
    side_sockets : socket_collection

    def __init_subclass__(cls):
        cls.in_sockets   = socket_collection.construct_if_not('in_sockets',   Direction='in',   Groups=getattr(cls,'in_sockets',[]))
        cls.out_sockets  = socket_collection.construct_if_not('out_sockets',  Direction='out',  Groups=getattr(cls,'out_sockets',[]))
        cls.side_sockets = socket_collection.construct_if_not('side_sockets', Direction='side', Groups=getattr(cls,'side_sockets',[]))

    context = context.construct(include=['meta_graph','root_graph','subgraph'],as_name='node')
    def _context_walk_(self):
        with self.context.register():
            self.in_sockets._context_walk_()
            self.out_sockets._context_walk_()
            self.side_sockets._context_walk_()

    def __init__(self,/,*,default_sockets:bool = False):
        self.context = self.context(self)
        self.In_Sockets   = self.in_sockets   #Consider mandating this structure def as capital
        self.Out_Sockets  = self.out_sockets  
        self.Side_Sockets = self.side_sockets 
        self.in_sockets   = self.in_sockets()
        self.out_sockets  = self.out_sockets()
        self.side_sockets = self.side_sockets()
        if default_sockets:
            self.default_sockets()

    def default_sockets(self):
        self.in_sockets.default_sockets()
        self.out_sockets.default_sockets()
        self.side_sockets.default_sockets()

class node_collection(BaseModel, typed_collection_base, ConstrBase,Hookable):
    _io_bin_name_  = 'node'
    _io_dict_like_ = True
    _io_blacklist_ = ['data']

    _constr_bases_key_  = 'node_collection'
    _constr_call_post_  = ['__io_setup__']
    _constr_join_dicts_ = ['_hooks']
    _constr_join_lists_ = ['_io_blacklist_','_io_whitelist_','_constr_call_post_']

    @property
    def Bases(self)->dict[str,Any]:
        return self.context.root_graph.module_col.items_by_attr('_io_bin_name_','g_node')

    data : list[node_archtype]

    context = context.construct(include=['meta_graph','root_graph','subgraph'])
    def _context_walk_(self):
        with self.context.register():
            for v in self.data:
                v._context_walk_()

    def __init__(self):
        self.context = self.context(self)
        self._data   = OrderedDict()


class subgraph(BaseModel, item_base, ConstrBase,Hookable):
    ''' Container for nodes, links'''
    _io_bin_name_  = 'subgraph'
    _io_blacklist_ = ['links']

    _constr_bases_key_ = 'subgraph'
    _constr_call_post_ = ['__io_setup__']
    _constr_join_dicts_ = ['_hooks']
    _constr_join_lists_ = ['_io_blacklist_','_io_whitelist_','_constr_call_post_']

    nodes : flat_col[node_collection]
    links : typed_collection_base[link]
        #Retroactivly Populated via subcollection[link] on sockets
        # In memory only

    context = context.construct(include=['meta_graph','root_graph'],as_name = 'subgraph')
    def _context_walk_(self):
        with self.context.register():
            self.nodes._context_walk_()

    def __init__(self,):
        self.context = self.context(self)
        with self.context.register():
            self.links   = link_collection()
            self.nodes   = node_collection()


class subgraph_collection[SubgraphType=subgraph](BaseModel, collection_base, ConstrBase,Hookable):
    _io_bin_name_ = 'subgraph'
    _io_dict_like_ = True
    _io_blacklist_ = ['data']

    _constr_bases_key_ = 'subgraph_collection'
    _constr_call_post_ = ['__io_setup__']
    _constr_join_dicts_ = ['_hooks']
    _constr_join_lists_ = ['_io_blacklist_','_io_whitelist_','_constr_call_post_']
    
    Base = subgraph
    data : dict[subgraph]


    def __init__(self):
        self.context = self.context(self)
        self._data   = OrderedDict()


    context = context.construct(include=['meta_graph','root_graph','subgraph'])
    def _context_walk_(self):
        with self.context.register():
            for v in self.data:
                v._context_walk_()
    
from .struct_module_collections import (local_module_collection, 
                                        Global_Module_Pool)         #Singleton inst of global_module_collection

class graph(BaseModel, ConstrBase,Hookable):
    _io_bin_name_  = 'graph'
    _io_blacklist_ = ['active','g_module_col']

    _constr_call_post_ = ['__io_setup__']
    _constr_join_dicts_ = ['_hooks']
    _constr_join_lists_ = ['_io_blacklist_','_io_whitelist_','_constr_call_post_']
    _constr_bases_key_ = 'graph'

    _nodes      : flat_bin[node]
    _subgraphs  : flat_bin[subgraph]

    Global_Module_Pool = Global_Module_Pool
    
    label : str
    
    active       : bool = False
    module_col   : local_module_collection 
    
    subgraphs : flat_col[subgraph_collection]
    

    context = context.construct(include = ['meta_graph'],as_name = 'root_graph')
    def _context_walk_(self):
        with self.context.register():
            self.subgraphs._context_walk_()

    def __init__(self,module_iten:dict=None):
        self.context    = self.context(self)
        self.module_col = local_module_collection(module_iten=module_iten)
        self.subgraphs  = subgraph_collection()


class graph_collection(BaseModel, collection_base, ConstrBase,Hookable):
    _io_bin_name_ = 'graph'
    _io_dict_like_ = True
    _io_blacklist_ = ['data']

    _constr_bases_key_ = 'graph_collection'
    _constr_call_post_ = ['__io_setup__']
    _constr_join_dicts_ = ['_hooks']
    _constr_join_lists_ = ['_io_blacklist_','_io_whitelist_','_constr_call_post_']

    Base = graph

    data : list[subgraph]

    context = context.construct(include=['meta_graph'])
    def _context_walk_(self):
        with self.context.register():
            for v in self.data:
                v._context_walk_()

    def __init__(self):
        self._data   = OrderedDict()
        self.context = self.context(self)


class meta_graph(BaseModel, ConstrBase,Hookable):
    ''' Should have a single instance, holds graphs, sets active. If more than one instance the latest active's modules are used. '''
    ''' Current design limitation of structure for flexibility to instnace manually in user modules. '''
    _constr_call_post_ = ['__io_setup__']
    _constr_join_dicts_ = ['_hooks']
    _constr_join_lists_ = ['_io_blacklist_','_io_whitelist_','_constr_call_post_']
    _constr_bases_key_ = 'metagraph'

    Global_Module_Pool = Global_Module_Pool

    _graphs  : flat_bin[graph]
    graphs   : flat_col[graph_collection]

    context = context.construct(as_name='meta_graph')
    def _context_walk_(self):
        with self.context.register():
            self.graph._context_walk_()

    def __init__(self):
        self.graphs = graph_collection() 
        self.context = self.context(self)

    def _run_tests(self):
        self.Global_Module_Pool.load()
        for mod in self.Global_Module_Pool:
            print(f'TESTING: {mod.UID} : {mod.Version}')
            mod._run_tests(self)

    def _Set_As_Active_Construction(self,graph_inst:graph):
        ''' Construct in place all types using modules list '''
        ''' This does limit the active graph count to 1, inactive graphs will have to disable hooks '''

        #Fuggly, break into more functions with contextual stuff.

        for x in self.graphs:
            x.active = False
        graph_inst.active = True

        module_col = graph_inst.module_col
        
        mixins = defaultdict(list)
        for x in module_col.mixins:
            key = getattr(x,'_constr_bases_key_','_uncatagorized')
            mixins[key].append(x)
        
        t = Bases.set(mixins)

        link.Construct(recur=False)
        link_collection.Construct(recur=False)
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

        for item_class in graph_inst.module_col.items:
            item_class.Construct(recur=False)
            #This allows mixins to target multiple levels of construction, 
            #In this case first level subtypes such as exec_nodes vs meta_nodes

        Bases.reset(t)


def _Load_Types():
    ''' Fullfill object types post loader, pre-import'''
    items  = defaultdict(dict)

    for x in Global_Module_Pool.items:
        key = getattr(x,'_constr_bases_key_','_uncatagorized')
        items[key] = x

    node_archtype.types   = items['node']
    socket_archtype.types = items['socket']