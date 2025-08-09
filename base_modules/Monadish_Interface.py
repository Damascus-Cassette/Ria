from .utils.statics         import get_data_uuid, get_file_uid, INVALID_UUID
from .Execution_Types       import _mixin, item
from ..statics              import _unset
from ..models.struct_module import module
from .Execution_Types       import socket_shapes as st

from typing import Self

from typing import TypeAlias

class main(module):
    ''' A monad-like interface for creating graphs'''
    UID     = 'Monadish_Interface'
    Version = '1.0'

    class node_mixin(_mixin.node):
        
        def _monadish_fork_()->Self:
            ...

        def _monadish_replace_(self,socket_dir='in')->Self:
            ...
        def _monadish_append_(self,socket_dir='in')->Self:
            ...
        def _monadish_merge_(self, other)->Self:
            ...

        @classmethod
        def M(cls,socket_values)->Self:
            inst = cls(default_sockets=True)
            #sockets -> links
            #values  -> set on socket
            ...

        #Figuring best use case for non-single node merge/operations is a bit odd
        _monadish_or_ : item.node
        def __or__(self,other,src = None):
            if src is None:
                src = getattr(self._monadish_or_)

            src_inst = src.M()
        
    class socket_mixin(_mixin.socket):

        _monadish_or_ : TypeAlias = item.node
        def __or__(self,other,src = None)->_monadish_or_:
            if src is None:
                src = getattr(self._monadish_or_)

            src_inst = src.M(self,other)

            #Source from _monad_or_src_!
            #but, may need to take into account the socket types, perhaps storing them on that?
            #Some will be generic, some others may need custom mapping.
            #others will not have correct comparisons.
            #create new common OR node of self all or other, must have matching socket count.
            #Left priority
            
            #Monads-like will typically be called on the output socket. So the source can be so. WIth exceptions but on the socke            
            ...
        

    
