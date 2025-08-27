from contextvars import ContextVar
from enum import Enum

class This(Enum):
    ANY                = None
    LOCAL              = None
    CLIENT             = None
    WORKER             = None
    MANAGER            = None

class Ext(Enum):
    CLIENT_ANY         = None
    CLIENT_UNTRUSTED   = None
    CLIENT_TRUSTED     = None
    WORKER_ANY         = None
    WORKER_UNTRUSTED   = None
    WORKER_TRUSTED     = None

    MANAGER_ANY         = None
    MANAGER_UNTRUSTED   = None
    MANAGER_TRUSTED     = None

    SELF               = None

This_Mode  = ContextVar('this_mode',  default = This.LOCAL)

Other_Con  = ContextVar('other_con',  default = None )
Other_Rep  = ContextVar('other_rep',  default = None )
Other_Mode = ContextVar('other_mode', default = None )


def con_match(this,other):
    ''' Construct a context matcher '''
    def matcher(this_mode=None,_other=None):
        if not isinstance(this, (tuple,list)): this  = (this ,)
        if not isinstance(other,(tuple,list)): other = (other,)
        if this_mode is None:  this_mode  = This_Mode.get()
        if other_mode is None: other_mode = Other_Mode.get()
        
        for x in this:
            if x not in this_mode:  return False
        
        for x in other:
            if x not in other_mode: return False
        
        return False
    return matcher

class manager():
    ''' Manager entity, IO called with a related class that signs itself, manager gets foreign_rep of and handles from there '''
    local = This.MANAGER

    @io_overload()
    def func(self,*args,**kwargs):
        raise Exception('MODE IS UNDEFINED!', context_mode.get(), context_con.get() )

    func = io_overload()

    @func.r(key = 'lc', self = This.LOCAL) #Assumes local since no con definition
    def func():
        ...

    @func.r(key = 'verify', self = This.MANAGER, local = True)
    def _func(self, args, kwargs):
        ...
 
    @func.r(key = 'mg', self = This.MANAGER, local = True, inherit = True )
    def _func(self,any_con, any_rep, args, kwargs):
        ...
 
    @func.r(key = 'mg', self = This.MANAGER, local = True, con = Ext.CLIENT_TRUSTED, address = '{}/five' ) #Specified path is otherfunc -> call this func and this func filters to only be client signed
    def _func(self,client_con, client_rep, args, kwargs):
        ...

    @func.r(self = (This.MANAGER, This.CLIENT), con = Ext.ANY, inherit = True)
    def _func(self,any_con, any_rep, args, kwargs):
        ...

    #This referse to an instances' mode
    #local = True refers to a lack of connections, if con_inherit = True and local, the e_con and e_rep may be None and could be any types
    #If local and con are defined, the contextual con must be of that mode.
    #when a pooled func is called directly, it assumes undefined. The root function, which may throw an error.
    #Keys declare a namespace to force that func call.
    # Ie @func.r(key = 'mg') -> func.mg().
    # In cases with multiple keys and a key being asked for, it uses first match context (in order of adding)

# This feels very complicated for a complicated issue.
# I suspect though I wont use it to this extent often, and will try to seperate client facing commands from non-client facing commands\
# One thing that I have to find out is exposure of ports on different entities.
# perhaps a better option would be allowing the entities to wrap the functions themselves?

    @func.r('mg', This.CLIENT , Ext.MANAGER_ANY)                          #Specified path is otherfunc -> call this func and this func filters to only be client signed
    @func.r('mg', This.MANAGER, Ext.CLIENT_TRUSTED, address = '{}/five' )
    def _func(self, client_or_manager_con, client_or_manager_rep, *args, **kwargs):
        ''' This function runs in the above cases of this as client|local|manager '''

    @func.r('mg', con_match(This.MANAGER, Ext.CLIENT_TRUSTED), see_rep = True, address = '{var}/five' )                      
    def _func(self, client_con, client_rep, var):
        ...
