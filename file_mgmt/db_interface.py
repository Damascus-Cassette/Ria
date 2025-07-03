from typing      import Any,TypeAlias,get_type_hints
from contextlib  import contextmanager
from contextvars import ContextVar
from functools   import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import Session


from .settings       import settings_interface
from .db_struct      import Base
from .db_repo_base   import repo_interface_base,_transaction
from .db_repo        import (
        repo_user,
        repo_NamedFile,
        repo_NamedSpace,
        repo_File,
        repo_Space,
        repo_Export,
        repo_Session,
        )
from .db_repo import context as repos_context

class _unset:...

class db_interface():  
    _repo_base      : repo_interface_base
    repo_user       : repo_user
    repo_NamedFile  : repo_NamedFile 
    repo_NamedSpace : repo_NamedSpace 
    repo_File       : repo_File 
    repo_Space      : repo_Space 
    repo_Export     : repo_Export 
    repo_Session    : repo_Session 

    context : Any

    def __init__(self,settings:dict|str):

        self.context = self._construct_context(inherit_from = (repos_context,), cvars = {
            'platform':'default',
            })
        self.c_engine    = ContextVar('engine' ,   default = None)
        self.c_session   = ContextVar('session',   default = None)
        self.c_savepoint = ContextVar('savepoint', default = None)
        
        self._load_settings(settings)
        self._load_db()

        self._construct_repos_from_anno()
    
    def _load_settings(self,settings):
        if isinstance(settings,str):
            self.settings = settings_interface.load_file(settings, context=self.context)
        else:
            self.settings = settings_interface.load_data(settings, context=self.context)
        
    def _load_db(self):
        # self.settings.fetch(value-uid)
        db_p = self.settings.database._sqla_db_path
        self.engine = create_engine(db_p)
        Base.metadata.create_all(self.engine)

        return self.c_engine.set(self.engine)
    

        # if not self._db_check_lock(force):
        #     self._db_register_lock(use_atexit=True)
        # else:
        #     raise Exception('')
    # def _db_check_lock(self)->bool:
    #     ''' check if lock apart from current thread exists in database. If so no transaction can complete unless forced '''
    # def _db_register_lock(self,use_atexit)->None:
    #     ''' Register lock, add atexit command for removal of lock'''
    #     import atexit
    # def _db_unregister_lock(self)->None:
    #     ...

    def _construct_repos_from_anno(self):
        for k,th in self.__anno_resolved__.items():
            i = getattr(self,k,None)
            if issubclass(th,repo_interface_base) and not i:
                new_cls = self._construct_repo([th],self.context)
                setattr(self,k,new_cls)

    def _construct_context(self,cvars:dict,inherit_from=(object,)):
        items = {}
        for k,v in cvars.items():
            items[k] = ContextVar(k,default=v)

        return type('context',inherit_from,items)

    def _construct_repo(self,base_classes,context):
        session_manager = self.session_cm
        ret = type('repo_base', tuple(base_classes) , {
            'db_interface' : self, 
            'c_engine'     : self.c_engine, 
            'c_session'    : self.c_session,
            'c_savepoint'  : self.c_savepoint, 
            'context'      : context
            })
        _transaction.rewrap(ret,session_manager)
        return ret

    @property
    def __anno_resolved__(self):
        if not hasattr(self,'__anno_resolved_cache__'):
            self.__anno_resolved_cache__ = get_type_hints(self.__class__)
        return self.__anno_resolved_cache__

    @contextmanager
    def generic_cm(self,**kwargs):
        #User for settings generic attributes
        cust_tokens = {}
        try:
            for k,v in kwargs.items():
                if isinstance((cvar:=getattr(self.context,k,None)),ContextVar):
                    print(f'cvar {cvar} is being set to {v}')
                    cust_tokens[k] = cvar.set(v)
                # else:
                #     raise Exception('Context is missing ContextVar for: ',k)
            yield
        except:
            raise
        finally:
            for k,v in cust_tokens.items():
                cvar = getattr(self.context,k)
                cvar.reset(v)

    @contextmanager
    def repo_cm(
        self    ,
        User    = _unset,
        Session = _unset,
        Export  = _unset,
        Space   = _unset,
        File    = _unset):
        
        tokens = []
        try:
            if not User    is _unset:
                t1 = self.context.User   .set(User   )
                tokens.append(lambda: self.context.User.reset(t1))
            if not Session is _unset:
                t2 = self.context.Session.set(Session)
                tokens.append(lambda: self.context.Session.reset(t2))
            if not Export  is _unset:
                t3 =self.context.Export .set(Export )
                tokens.append(lambda: self.context.Export.reset(t3))
            if not Space   is _unset:
                t4 = self.context.Space  .set(Space  )
                tokens.append(lambda: self.context.Space.reset(t4))
            if not File    is _unset:
                t5 = self.context.File   .set(File   )
                tokens.append(lambda: self.context.File.reset(t5))
            yield
        except:
            raise
        finally:
            for l in tokens:
                l()

    def fill_context(
            self    ,
            User    = _unset,
            Session = _unset,
            Export  = _unset,
            Space   = _unset,
            File    = _unset):
        ''' Identical I->O for ensuring fetch of objects from context if not set'''
        #TODO: Make more generic with **qkwargs
        ret = []
        if not User    is _unset:
            if not User:
                ret.append(self.context.User   .get())   
            else:
                ret.append(User)
        if not Session is _unset:
            if not Session:
                ret.append(self.context.Session.get())
            else:
                ret.append(Session)
        if not Export  is _unset:
            if not Export:
                ret.append(self.context.Export .get()) 
            else:
                ret.append(Export)
        if not Space   is _unset:
            if not Space:
                ret.append(self.context.Space  .get())  
            else:
                ret.append(Space)
        if not File    is _unset:
            if not File:
                ret.append(self.context.File   .get())   
            else:
                ret.append(File)

        return tuple(ret)

    @contextmanager
    def session_cm(self,*args,**kwargs):
        if not getattr(self,'engine',None):
            self._load_db()

        if not self.c_session.get():
            self.c_session.set(Session(bind=self.engine, expire_on_commit = True))
            print('Creating Session!')

        session        = self.c_session.get()
        in_transaction = session.in_transaction()

        try:
            if in_transaction:
                _savepoint = session.begin_nested()
                token1 = self.c_session.set(session)
                token2 = self.c_savepoint.set(_savepoint)
                # token = self.c_session.set(_session)
                yield session
                _savepoint.commit()
            else:
                yield session
                session.commit()
                session.close()
                self.c_session.set(None)
        except:
            if in_transaction:
                _savepoint.rollback() 
            else:
                session.rollback()  
                session.close()
                self.c_session.set(None)
            raise

        finally:
            if in_transaction:
                self.c_session.reset(token1) 
                self.c_savepoint.reset(token2) 
