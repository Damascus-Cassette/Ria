
from enum import Enum
from contextvars import ContextVar
from typing import Any

class Int(Enum):
    ''' Internal Object '''
    LOCAL   = None
    MANAGER = None
    WORKER  = None
    CLIENT  = None
    CLI     = None

class Ext(Enum):
    ''' External Object & Descriptor (via Connection)'''
    MANAGER_ANY       = None
    WORKER_ANY        = None
    CLIENT_ANY        = None

    MANAGER_TRUSTED   = None
    WORKER_TRUSTED    = None
    CLIENT_TRUSTED    = None

    MANAGER_UNTRUSTED = None
    WORKER_UNTRUSTED  = None
    CLIENT_UNTRUSTED  = None


STATE     : Int                    = ContextVar('gl_state'    , default = Int.LOCAL)
requester : 'local_and_connection' = ContextVar('calling_item', default = None     )


class _def_dict_list(dict):
    def __missing__(self,key):
        self[key] = inst = []
        return inst

class connection_manager():
    def __init__(self):
        self.mapping = {
            Int.MANAGER.value : Manager, 
            Int.CLIENT.value  : Client ,
            Int.WORKER.value  : Worker , 
            }
        
        self.connections = _def_dict_list()
            #TODO: change to Collection w/ FileIO compatable basetypes
    
    def handle_incoming(self,con,msg)->'local_and_connection':
        ''' De-dupe incoming connections, create untrusted connection instances as required based on declared type '''
        #TODO
        return ...
    
    

class connection():    
    def __init__():
        ...

    def __get__(self,inst,inst_cls):
        self.container = inst
        return self

    @property
    def state(self):
        assert (self.container.state in Ext) or (self.container.state is Ext)
        return self.container.state
    
    
    def Get(self,):
        self.container

    def Post(self,):
        self.container

    def Patch(self,):
        self.container

    def Delete(self,):
        self.container


class local_and_connection():
    Is_Connection : bool
    Connection    : object[connection]

    @classmethod
    def _As_Connection(cls,):
        ''' Generate the as_connection object, which contains more methods for interaction 
        '''


    def __init_subclass__(cls):
        cls.As_Connection = cls._As_Connection()

        super().__init_subclass__()

    def generate_local():
        ...

class Worker(local_and_connection):
    def __init__(settings):
        ...

    next_message = None

    @api.get('echo')
    def echo(self,con,var):...

    @echo.get(key = 'get'. self.Int, requester=Ext.MANAGER_ANY)
    def echo(self,con,var):
        import time
        return {'msg':var, 'time':time, 'con_ip':con.ip, 'this_globals' : None, 'last_set_var' : self.next_message}

    @echo.set(key = 'get', self=Int, requester=Ext.MANAGER_ANY)
    def echo(self,con,var):
        self.next_message = var

class Manager(local_and_connection):
    '''Class that acts as both a connection and local object '''

    def __init__(settings):
        ...
    
    settings : Any|fileio

    workers  : list[Worker]
    state    = Int

    @api('echo')                        
    def echo_workers(self,con,var):
        ''' All functions enter into self class's context as requester when getting the function. Exited on return. This allows requester to be filled'''
        ''' Default, usually error or fallback handler. Best as explicit and short '''
        return 404

    @echo_workers.get(key = 'get_lc', self=Int, requester=Int) #Essentially Operating Locally. Can also inherit a connection???
    def _echo_worker(self, con:None, msg:str):
        ''' Local operation of the function, typically the non-abstracted logic '''
        res = []
        for x in self.workers():
            res.append(x.echo(msg))
        return res

    @echo_workers.get(key = 'get_int', self=Int, requester=Ext)
    def _echo_worker(self,con, msg):
        ''' Request from a connection to ping workers, 
        forward to local function in this case'''
        return self.echo_workers.get_lc(msg, _con = con)

    @echo_workers.get(key = 'get_ext', self=Ext, requester=Int)
    def _echo_worker(self,con, msg):
        ''' As a connection, '''
        return self.Connection.get('echo_worker', msg)


    @api('some_func')
    def some_func(self, con:None|Any, msg:str): 
        return 404

    @some_func.get(key = 'get', self=Int, requester=(Int,Ext), generate_self_ext = True)  
    def some_func(self, con:None|Any, msg:str):
        ''' generate_self_ext generates generic functions that send the request back to the manager and this original function'''
        res = []
        for x in self.workers():
            res.append(x.echo(msg))
        return res

    @some_func.set(key = 'set', self=Int, requester = Int)
    @some_func.set(key = 'set', self=Int, requester =(Int.CLI, Ext.CLIENT_TRUSTED), generate_self_ext = True)  #Generate shoudl only fill in the gaps of what is not covered, run after declaration complete
    def _some_func(self,con, msg):
        ...

    # @echo_workers.local_get_factory() #Factory produces identical funcs in ext->int and int->ext cases via similar to above logic. 
    # def some_func(self, con:None, msg:str):
    #     ''' Local operation of the function, typically the non-abstracted logic '''
    #     res = []
    #     for x in self.workers():
    #         res.append(x.echo(msg))
    #     return res
        
#why not use __get__ to route between the functions instead of going through a connection obj?