from contextvars import ContextVar
from enum import Enum

class Primary(Enum):
    ANY                 = None
    CLIENT              = None
    WORKER              = None
    MANAGER             = None
    CLI                 = None

class As_Con(Enum):
    ''' Meaning as a connection within the current thread '''
    ANY             = None
    CLIENT          = None
    WORKER          = None
    MANAGER         = None

class Ext_Con(Enum):
    ''' Meaning a connection from an external source '''
    CLIENT_ANY          = None
    CLIENT_UNTRUSTED    = None
    CLIENT_TRUSTED      = None

    WORKER_ANY          = None
    WORKER_UNTRUSTED    = None
    WORKER_TRUSTED      = None

    MANAGER_ANY         = None
    MANAGER_UNTRUSTED   = None
    MANAGER_TRUSTED     = None



Primary_Mode  = ContextVar('this_mode',  default = Primary.LOCAL)

Other_Con  = ContextVar('other_con',  default = None )
Other_Rep  = ContextVar('other_rep',  default = None )
Other_Mode = ContextVar('other_mode', default = None )

def con_match(this,other):
    ''' Construct a context matcher '''
    def matcher(this_mode=None,_other=None):
        if not isinstance(this, (tuple,list)): this  = (this ,)
        if not isinstance(other,(tuple,list)): other = (other,)
        if this_mode is None:  this_mode  = Primary_Mode.get()
        if other_mode is None: other_mode = Other_Mode.get()
        
        for x in this:
            if x not in this_mode:  return False
        
        for x in other:
            if x not in other_mode: return False
        
        return False
    return matcher


class _api():
    
    ...

class manager(api_cls):
    mode   : Primary  = Primary.ANY
    is_con : bool = False 

    connection_rep : Type
    connection_data_attrs = []
        #also inherits all overloaded functions
        #though no local versions

    @classmethod
    def as_connection(cls,connection,data):
        return cls.foreign_rep(connection,data)
        
    def __init__(self):
        ...
    
    @api('address/{var}/')
    def function(self,var): raise Exception('')

    @function.overload_get('lc', Primary.LOCAL)
    def _func(self, var):
        return 'I Trust Myself'
    
    @function.overload_get(Primary.MANAGER, Ext_Con.CLIENT_UNTRUSTED)
    def _func(self,client_con, client_rep, var): 
        return 'NO, I DONT TRUST YOU'

    @function.overload_get(Primary.MANAGER, (Ext_Con.CLIENT_TRUSTED, Primary.MANAGER)) #Inherits connection automatically
    def _func(self,client_con, client_rep, var): 
        return var
    @function.overload(Primary.MANAGER, Primary.MANAGER, inherit_connection = True) #Above's second case eq to this
    def _func(self,client_con, client_rep, var): 
        return var

    @function.overload_get(Primary.MANAGER, Primary.CLI)
    def _func(self, var): 
        return 'Hello Local User!'


    @function.overload_get('mg_get', self=As_Con.MANAGER, _from=Primary.CLIENT) #meaning manager instance is a connection, client class is an internal one
    def _func(self, con, rep, var):
        return con.responce_get(var)

    @function.overload_put('mg_put', self=As_Con.MANAGER, _from=Primary.CLIENT) #meaning manager instance is a connection, client class is an internal one
    def _func(self, con, api, var, data):
        return api.responce_put(con,var = var, data = data)

    @function.overload_put('mg_put', self=(Primary.ANY, As_Con.ANY), _from=(Primary.ANY, As_Con.ANY)) #Any object calling this function would match 
    def _func(self, con, var):
        return con.responce_put(var)


### That's gettign weird, let's try an actual example

class worker (f_rep):
    mode = Primary.WORKER
    
    @api('ping')
    def ping(self,con,rep,):raise Exception('Did not find!')

    @ping.ol_get('wk', self = As_Con,  _from = Primary)
    def _ping_get(self, _from : manager):
        return self.con.get('ping',_from.foreign_rep())

    @ping.ol_get('wk', self = Primary, _from = Ext_Con, see_con_rep = True)
    def _ping_get(self, _from : manager.connection ):
        import time
        return {'recieved':str(time.time()),'from':(_from.ip, _from.label, _from.state.value)} 

    @ping.ol_get('wk', self = Primary, _from = Primary, see_con_rep = True)
    def _ping_get(self,):
        ''' This would be two instances calling each other in a 'local' context, ie working locally w/ two managers'''
        import time
        return {'recieved':str(time.time())}
    
    @api.get('echo')
    def echo(self, _from:connection, message): 
        import time
        return {'Message':message,'recieved':str(time.time()),'from':(_from.ip, _from.label, _from.state.value)} 

class manager(f_rep):
    mode = Primary.MANAGER
    
    workers : list[worker.connection]
    
    ping_workers = api('/ping_workers')
    @ping_workers.get()
    def _ping_workers(self):
        for x in self.workers:
            print(x.ping())

    echo_workers = api('/echo_workers')
    @echo_workers.get()
    def _echo_workers(self,message):
        for x in self.workers:
            print(x.echo(message))






    