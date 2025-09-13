from enum import Enum

class Entity_Types(Enum):
    WORKER  = 'WORKER'
    CLIENT  = 'CLIENT' 
    MANAGER = 'MANAGER'
    UNDEC   = 'UNDECLARED'

class Trust_States(Enum):
    TRUSTED   = 'TRUSTED'
    UNTRUSTED = 'UNTRUSTED'

class Connection_States(Enum):
    CONNECTED  = 'CONNECTED'
    CLOSED     = 'CLOSED'
    ERROR      = 'ERROR'
    NEVER_CON  = 'NEVER_CON'

class Worker_State(Enum):
    SLEEP     = 'SLEEP'
    WORKING   = 'WORKING'
    AVAILABLE = 'AVAILABLE'
    UNKNOWN   = 'UNKNOWN'