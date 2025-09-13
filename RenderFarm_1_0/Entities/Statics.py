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
        
    JOB            = 'JOB'        # Request, Accept, Deny, Failed, Confirm ect 
    JOB_STATE      = 'JOB_STATE'  # Complete, Failed, Started, ect
        # topic of {ITEM}       is actionable
        # topic of {ITEM}_State is observational
        # Observational (IE, disconnect w/ timeout) MAY also be actionable
        
    TASK           = 'TASK'       
    TASK_STATE     = 'TASK_STATE' 

    GRAPH          = 'GRAPH'
    GRAPH_STATE    = 'GRAPH_STATE'

    CACHE          = 'CACHE'
    CACHE_STATE    = 'CACHE_STATE'


class Admin_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions '''
    VERIFY   = 'VERIFY'

class Misc_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions '''
    ECHO = 'ECHO'
    PING = 'PING'

class VALUE_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions '''
    RESET = 'RESET'
    SET   = 'SET'

class CRUD_Message_Actions(Desc_Enum):
    ''' CUD & REQUEST -> Worker; CONFIRM_HASH_RESULT -> Manager '''

    CREATE      = 'CREATE'
    BULK_CREATE = 'BULK_CREATE'

    UPDATE      = 'UPDATE'
    BULK_UPDATE = 'BULK_UPDATE'

    DELETE      = 'DELETE'
    BULK_DELETE = 'BULK_DELETE'

    CONFIRM_ITEN_REQUEST  = ('CONFIRM_ITEN_REQUEST',  'Request Itenerary of items')
    CONFIRM_ITEN_RESPONCE = ('CONFIRM_ITEN_RESPONCE', 'Return  Itenerary of items')

    CONFIRM_HASH_REQUEST  = ('CONFIRM_HASH_REQUEST',  'Request uuid-hash of data-set with shared method')
    CONFIRM_HASH_RESPONCE = ('CONFIRM_HASH_RESPONCE', 'Return  uuid-hash of data-set with shared method')

class Action_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions that result in change '''
    REQUEST             = ('REQUEST'          , "Request for Action" )

    ACCEPT              = ('ACCEPT'           , "Confirming action to start" )
    DENY                = ('DENY'             , "Denying action" )

    COMPLETED           = ('COMPLETED'        , "Finished requested action, Note: Not the same as a tasks completion, as a task can discover dependent tasks and return early " )

    FAILED              = ('FAILED'           , "Responce from a fully failed Task" )
    FAILED_REQ_RETRY    = ('FAILED_REQ_RETRY' , "Responce from a partially failed Task")    

class ActionState_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions that DO-NOT result in action '''

    UNKNOWN             = 'UNKNOWN'
    STARTED             = ('STARTED'          , "Begining a job, such as setting up env" )
    PROCESSING          = ('PROCESSING'       , "Processing a job" )
    FINISHING           = ('FINISHING'        , "Completing a job, dumping to disc and evaluating hashes pre-upload as required" )
    SUBMITTING          = ('SUBMITTING'       , "Submiting a job's files to the manager" )
    COMPLETED           = ('COMPLETED'        , "Completion of a job and all submission to the manager" )

    FAILED_RETRY        = ('FAILED_RETRY'     , "Failed a task will retry" )
    FAILED              = ('FAILED'           , "Failed a task full stop" )

    

TOPIC_ACTION_MAP = {
    Message_Topics.ADMIN         : Admin_Message_Actions ,
    Message_Topics.MISC          : Misc_Message_Actions  ,
    # Message_Topics.JOB           : ,
    # Message_Topics.TASK          : ,
    # Message_Topics.GRAPH         : ,
    # Message_Topics.CACHE         : ,
}

