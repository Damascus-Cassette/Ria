from enum import Enum

class Entity_Types(Enum):
    WORKER  = 'WORKER'
    CLIENT  = 'CLIENT' 
    MANAGER = 'MANAGER'
    UNDEC   = 'UNDECLARED'


class Trust_State(Enum):
    TRUSTED   = 'TRUSTED'
    UNTRUSTED = 'UNTRUSTED'