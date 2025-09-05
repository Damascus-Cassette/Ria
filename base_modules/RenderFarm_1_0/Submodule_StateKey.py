from ..Execution_Types    import _mixin, _item
from ..utils.statics      import get_data_uuid
from .Env_Variables       import Backwards_Context
from ...statics           import _unset

from typing import TypeAlias

dep_keys   : TypeAlias = tuple
struct_key : TypeAlias = str

local_state_key      : TypeAlias = str

contextual_state_key : TypeAlias = str


class socket_mixin(_mixin.socket):

    _struct_key   : struct_key
    _context_deps : dep_keys

    @property
    def state_key(self):
        return self.context.node.state_key

    def local_state_key(self)->local_state_key:
        ''' Local state of this socket in a hashable form. 
        Does not include links (part of structural), 
        But local data can change in relation to links' presence (ie unused Default_Value)
            - This is the default implamentation assumption 
        Best way to think about this is get_data_uuid(all used values)
        '''
        
        if self.dir.upper != 'OUT':
            if len(self.links):
                return 'UPSTREAM' 
                #As noted, by default link_values flatten local_state.
            return get_data_uuid(self.Default_Value) 
                #May want to use resolution chain
        
        return self.label

        #Above MAY need to be more unique, though I think the stuructral access is OK

    def init_state_components(self):
        if self.dir.upper() != 'OUT':
            return self.init_state_components_insockets
        return self.init_state_components_outsockets

    def init_state_components_outsockets(self):
        ''' Called on out sockets, forwards quiry to node (which observes local state)
            - ~note: this method causes a structural_key change if a sibling socket's local_state_key is different.~
                - UPDATE: preventing this by not adding output socket's state directly to the node's structural state
                - This may create different problems later in specific circustamnces
                    - ie when a node's outputs affect each socket's execution
                    - In situations like above, the output's affects should be factored into the **node's** local_state_key 
        '''
        assert self.dir.upper() == 'OUT'
        struct_key, deps =  self.context.node.init_state_components()
        struct_key = struct_key + self.local_state_key() + self.dir
        
        deps = tuple(sorted(list(set(deps))))
        struct_key = get_data_uuid(struct_key)

        self._struct_key = struct_key
        self._context_deps = deps

        return struct_key, deps
        

    def init_state_components_insockets(self)->tuple[struct_key,dep_keys]:
        ''' Called on in/side sockets, gets local socket and passing along quiry  '''
        assert self.dir.upper() != 'OUT'

        deps = tuple()
        struct_key = ''

        for link in self.links:
            _struct_key, _deps = link.out_socket.init_state_components_outsockets()
        
            struct_key = struct_key + _struct_key
            deps = deps + _deps

        deps = tuple(sorted(list(set(deps))))
        struct_key = get_data_uuid(struct_key)

        self._struct_key = struct_key
        self._context_deps = deps

        return struct_key, deps


class socket_collection_mixin(_mixin.socket_collection):

    # def local_state_key(self)->local_state_key:
    #     ''' called on out_sockets only '''
    #     local_state_key = ''

    #     for socket in self:
    #         local_state_key =+ socket.local_state_key

    #     return get_data_uuid(local_state_key)

    def init_state_components(self)->tuple[struct_key,dep_keys]:
        assert self.Direction.upper() != 'OUT'
        
        struct_key = ''
        deps = tuple()
        for socket in self:
            _struct_key, _deps = socket.init_state_components_insockets()
            struct_key = struct_key + _struct_key
            deps = deps + _deps

        deps = tuple(sorted(list(set(deps))))
        struct_key = get_data_uuid(struct_key)

        # self.struct_key = struct_key
        # self.deps = deps

        return struct_key, deps


class node_mixin(_mixin.node):
    _struct_key   : struct_key = _unset
    _context_deps : dep_keys   = _unset

    @property
    def state_key(self):
        if self._struct_key is _unset:
            self.init_state_components()

        state_key = self._struct_key
            #seeding state_key
        
        c_keys = [*Backwards_Context.get().keys()]
        for key in self._context_deps:
            if key not in c_keys  :
                raise Exception(f'Unconstrained Context Error with key: {key}, node: {self.context.Repr()}', )

            val = Backwards_Context.get()[key].get()

            if val is _unset:
                raise Exception(f'Unset Context Error with key: {key}, node: {self.context.Repr()}', )

            state_key = struct_key + get_data_uuid(val)

        return get_data_uuid(state_key)

    def local_state_key(self)->local_state_key:
        ''' Get this node's local state key, local untracked values that affect execution into a hashable format.
        Does not include sockets and links (contributers of struct_key)
        Exceptions to Change:
            - When values that are local to the node are **not** in sockets
            - When output sockets's affect execution
        '''
        return 'DEFAULT'

    def init_state_components(self,)->tuple[struct_key,dep_keys]:
        #Structurally, what is this key backwards_context vars does this depend on
        local_state = self.local_state_key()
        
        struct_key = local_state
        deps = tuple()

        _struct_key, _deps = self.in_sockets.init_state_components()
        struct_key = struct_key + _struct_key
        deps = deps + _deps
        
        _struct_key, _deps = self.side_sockets.init_state_components()
        struct_key = struct_key + _struct_key
        deps = deps + _deps

        # _struct_key = self.out_sockets.local_state_key()
        # struct_key =+ _struct_key
        # # deps = deps + _deps

        deps = self.change_context_dep_keys(tuple(sorted(list(set(deps)))))
        struct_key = get_data_uuid(struct_key)

        self._struct_key   = struct_key
        self._context_deps = deps

        return struct_key, deps
    
    def change_context_dep_keys(self,deps:dep_keys)->dep_keys:
        ''' Contextual add/remove dependencies from passing downstream
        Zone-Start should add    a key based on the zone set
        Zone-End   should remove a key based on the zone set
            - Context variables should not be unconstrained forward past the spawner.
            - Compilation is where the Backwards_Context is actuallly changed (as state_key is accessed in compilation & execution)
        '''
        return deps
    

_statekey_mixins_ = [
    socket_mixin,
    socket_collection_mixin,
    node_mixin,
]    
_statekey_items_  = []   
_statekey_tests_  = []
