from enum import Enum
from typing import Self, Annotated

class Desc_Enum(Enum):
    def __new__(cls, value, desc=None, user_desc=None)->Self:
        new = object.__new__(cls)
        new._value_     = value

        new.desc      = desc
        if user_desc: new.user_desc = user_desc
        else:         new.user_desc = desc

        return new


######## ENTITY DEFINITION ########

class Entity_Types(Desc_Enum):
    ''' Integral Types '''
    WORKER  = ('WORKER',     'Processing Entity'                             )
    MANAGER = ('MANAGER',    'Managment Entity'                              )
    CLIENT  = ('CLIENT' ,    'User Entity'                                   )
    UNDEC   = ('UNDECLARED', 'Unkown Entity via browser or malformed header' )


######## ENTITY STATE DEFINITION ########

class Trust_States(Desc_Enum):
    ''' Decided Foreign Entity States '''
    TRUSTED   = 'TRUSTED'
    UNTRUSTED = 'UNTRUSTED'

class Connection_States(Desc_Enum):
    ''' Observed Foreign Entity States '''
    NEVER_CON  = 'NEVER_CON'

    CONNECTED  = 'CONNECTED'
    CLOSED     = 'CLOSED'
    ERROR      = 'ERROR'


class Worker_PrimaryShared_States(Desc_Enum):
    ''' Worker -> Manager Declared States '''
    UNKNOWN     = 'UNKNOWN'

    SLEEP       = 'SLEEP'
    WORKING     = 'WORKING'
    AVAILABLE   = 'AVAILABLE'
    UNAVAILABLE = 'UNAVAILABLE'

class Manager_PrimaryShared_States(Desc_Enum):
    ''' Worker -> Manager Declared States '''
    UNKNOWN     = 'UNKNOWN'

    SLEEP       = 'SLEEP'
    WORKING     = 'WORKING'
    AVAILABLE   = 'AVAILABLE'
    UNAVAILABLE = 'UNAVAILABLE'


######## MESSAGE DEFINITION ########

class Message_Topics(Desc_Enum):
    ''' Worker <-> Manager Websocket Topics '''
    ADMIN          = 'ADMIN'
    MISC           = 'MISC'

    MANAGER_STATE  = 'MANAGER_STATE'
    WORKER_STATE   = 'WORKER_STATE' 
        
    # JOB            = 'JOB'        # Request, Accept, Deny, Failed, Confirm ect 
    # JOB_STATE      = 'JOB_STATE'  # Complete, Failed, Started, ect
        # topic of {ITEM}       is actionable
        # topic of {ITEM}_State is observational
        # Observational (IE, disconnect w/ timeout) MAY also be actionable
        
    # TASK           = 'TASK'       
    # TASK_STATE     = 'TASK_STATE' 

    # GRAPH          = 'GRAPH'
    # GRAPH_STATE    = 'GRAPH_STATE'

    # CACHE          = 'CACHE'
    # CACHE_STATE    = 'CACHE_STATE'

class Admin_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions '''
    VERIFY   = 'VERIFY'

class Misc_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions '''
    ECHO = 'ECHO'
    PING = 'PING'

class State_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions '''
    RESET = 'RESET'
    SET   = 'SET'

class Task_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions that result in change '''
    REQUEST             = ('REQUEST'          , "" )
    ACCEPT              = ('ACCEPT'           , "" )
    DENY                = ('DENY'             , "" )
    FAILED              = ('FAILED'           , "" )
    FAILED_REQ_RETRY    = ('FAILED_REQ_RETRY' , "" )

    CONFIRMATION        = ('CONFIRMATION'     , "" )

class TaskState_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions that Do NOT result in change '''
    STARTED             = ('STARTED'          , "" )
    PROCESSING          = ('PROCESSING'       , "" )
    FINISHING           = ('FINISHING'        , "" )
    SUBMITTING          = ('SUBMITTING'       , "" )
    COMPLETED           = ('COMPLETED'        , "" )

    FAILED_RETRY        = ('FAILED_RETRY'     , "" )
    FAILED              = ('FAILED'           , "" )


TOPIC_ACTION_MAP = {
    Message_Topics.ADMIN         : Admin_Message_Actions ,
    Message_Topics.MISC          : Misc_Message_Actions  ,
    Message_Topics.MANAGER_STATE : State_Message_Actions ,
    Message_Topics.WORKER_STATE  : State_Message_Actions ,
    # Message_Topics.JOB           : ,
    # Message_Topics.TASK          : ,
    # Message_Topics.GRAPH         : ,
    # Message_Topics.CACHE         : ,
}

