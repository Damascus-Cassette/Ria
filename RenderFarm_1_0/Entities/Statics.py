from enum import Enum
from typing import Self, Annotated

class Desc_Enum(Enum):
    def __new__(cls, value, desc=None, bound_follow:Enum=None, actionative = False)->Self:
        new = object.__new__(cls)
        new._value_     = value

        new.desc         = desc
        new.bound_follow = bound_follow
        new.actionative  = actionative

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

class Client_PrimaryShared_States(Desc_Enum):
    ''' Worker -> Manager Declared States '''
    UNKNOWN     = 'UNKNOWN'
    OTHER       = 'OTHER'
    SUBMITTING  = 'SUBMITTING'
    DOWNLOADING = 'DOWNLOADING'

######## MESSAGE DEFINITION ########

class Admin_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions '''
    VERIFY   = 'VERIFY'

class Misc_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions '''
    ECHO = 'ECHO'
    PING = 'PING'

class VALUE_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket Actions '''
    RET   = 'RET'
    SET   = 'SET'
    RESET = 'RESET'

class STATE_Message_Actions(Desc_Enum):
    ''' Worker <-> Manager Websocket State Declarations '''
    DECLARE = 'DECLARE'


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


class FILEDB_Message_Tables(Desc_Enum):
    USER        = 'USER'
    SESSION     = 'SESSION'

    IMPORT      = 'IMPORT'
    EXPORT      = 'EXPORT'
    VIEW        = 'VIEW'

    SPACE       = 'SPACE'
    NAMED_SPACE = 'NAMED_SPACE'

    FILE        = 'FILE'
    NAMED_FILE  = 'NAMED_FILE'


class FILEDB_Message_Actions(Desc_Enum):
    ''' CUD & REQUEST -> Worker; CONFIRM_HASH_RESULT -> Manager '''

    CREATE           = ('CREATE'            , 'Create DB Entry, must include info to populate' )
    BULK_CREATE      = ('BULK_CREATE'       , '' )

    UPDATE           = ('UPDATE'            , 'When applied to spaces/files, returns diffed structure.' )
    BULK_UPDATE      = ('BULK_UPDATE'       , '' )

    DELETE           = ('DELETE'            , 'N/A for files/spaces ' )
    BULK_DELETE      = ('BULK_DELETE'       , '' )

    OPEN             = ('OPEN'              , 'Only available for SESSION & VIEW') #When file/space, create withheld asc ID. When view, create and return view 
    BULK_OPEN        = ('BULK_OPEN'         , '' )

    CLOSE            = ('CLOSE'             , 'Only available for SESSION & VIEW' )
    BULK_CLOSE       = ('BULK_CLOSE'        , '' )

    CLEANUP          = ('CLEANUP'           , 'Forces an immediate cleanup operation on target objects children')
    CLEANUP_BULK     = ('CLEANUP_BULK'      , '')

    DIFF             = ('DIFF'              , 'Find if the manager contains the submitted hash in the target table' )
    DIFF_BULK        = ('DIFF_BULK'         , 'same as DIFF, in tuples of `[hash,table]` ' )
    
    DIFF_STRUCT      = ('DIFF_STRUCT'       , 'Diff a space via analgous dict structure, Return filelist that must be uploaded' )
    DIFF_STRUCT_BULK = ('DIFF_STRUCT_BULK'  , '' )
    
    QUERY            = ('QUERY'             , 'Find item id by asc information' )

    EXPOSE           = ('EXPOSE'            , 'Expose/Create folder struct of space/file specified. Returns value')
    UPLOAD           = ('UPLOAD'            , 'Upload a file, hash must be attached. ' )
    BULK_UPLOAD      = ('BULK_UPLOAD'       , 'Upload files/spaces, hash must be mapped to data' )

    DOWNLOAD         = ('DOWNLOAD'          , 'Download file/space ' )
    BULK_DOWNLOAD    = ('BULK_DOWNLOAD'     , 'Download bulk files/spaces' )
    

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

class Message_Topics(Desc_Enum):
    ''' Worker <-> Manager Websocket Topics. Third value is bound responce types '''

    ADMIN          = ('ADMIN'        ,'', Admin_Message_Actions      ,True)
    MISC           = ('MISC'         ,'', Misc_Message_Actions       ,True)

    DATA           = ('DATA'         ,'', VALUE_Message_Actions      ,True)
    CRUD           = ('CRUD'         ,'', CRUD_Message_Actions       ,True)

    FILE_DB        = ('FILE_DB'      ,'', FILEDB_Message_Actions     ,True)

    MANAGER_STATE  = ('MANAGER_STATE','', STATE_Message_Actions )
    WORKER_STATE   = ('WORKER_STATE' ,'', STATE_Message_Actions ) 
    CLIENT_STATE   = ('CLIENT_STATE' ,'', STATE_Message_Actions ) 
        
    JOB            = ('JOB'          ,'', Action_Message_Actions      ,True) # Request, Accept, Deny, Failed, Confirm ect 
    JOB_STATE      = ('JOB_STATE'    ,'', ActionState_Message_Actions ) # Complete, Failed, Started, ect
        
    TASK           = ('TASK'         ,'', Action_Message_Actions      ,True)
    TASK_STATE     = ('TASK_STATE'   ,'', ActionState_Message_Actions )

    GRAPH          = ('GRAPH'        ,'', Action_Message_Actions      ,True)
    GRAPH_STATE    = ('GRAPH_STATE'  ,'', ActionState_Message_Actions )

    CACHE          = ('CACHE'        ,'', Action_Message_Actions      ,True)
    CACHE_STATE    = ('CACHE_STATE'  ,'', ActionState_Message_Actions )

    # topic of {ITEM}       is actionable
    # topic of {ITEM}_State is observational
    # Observational (IE, disconnect w/ timeout) MAY also be actionable



TOPIC_ACTION_MAP = {
    Message_Topics.ADMIN         : Admin_Message_Actions ,
    Message_Topics.MISC          : Misc_Message_Actions  ,
    # Message_Topics.JOB           : ,
    # Message_Topics.TASK          : ,
    # Message_Topics.GRAPH         : ,
    # Message_Topics.CACHE         : ,
}

