from __future__ import annotations
from sqlalchemy import (Column, Boolean, ForeignKey, Integer, String, create_engine, Table)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Mapped, mapped_column
# from sqlalchemy.types import DateTime
from typing import ClassVar
from sqlalchemy import inspect

from datetime import date,datetime

if __name__ == '__main__':
    db_url = 'sqlite:///database.db'
    engine  = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id  = Column(String, primary_key=True)
    hid = Column(String)    

    #### Children ####
    mySessions: Mapped[list[Session]] = relationship(back_populates='myUser', cascade="all, delete", passive_deletes=True)
    myExports : Mapped[list[Export]]  = relationship(back_populates='myUser', cascade="all, delete", passive_deletes=True)
    myImports : Mapped[list[Import]]  = relationship(back_populates='myUser', cascade="all, delete", passive_deletes=True)
        #TODO TEST: passive_deletes may prevent a ORM Hook event from triggering because it's not loading the objects?

class Session(Base):
    __tablename__ = 'sessions'
    id  = Column(Integer, primary_key=True)
    hid = Column(String)    

    
    #### Parents ####
    myUserId  : Mapped[str]          = mapped_column(ForeignKey('users.id', ondelete="CASCADE"))
    myUser    : Mapped[User]         = relationship(back_populates='mySessions')

    #### Children ####
    myImports : Mapped[list[Import]] = relationship(back_populates='mySession', cascade="all, delete", passive_deletes=True)
    myExports : Mapped[list[Export]] = relationship(back_populates='mySession', cascade="all, delete", passive_deletes=True)
    myViews   : Mapped[list[View]]   = relationship(back_populates='mySession', cascade="all, delete", passive_deletes=True)
    
    #### Data ####
    isOpen    : Mapped[bool]         = mapped_column(default=True)
    
    #### Events ####
    def before_update(self):
        # Check for attribute change to update propigation
        # Usefull: https://stackoverflow.com/questions/43813451/how-can-you-automatically-check-if-one-or-more-attribute-is-modified-in-sqlalche
        insp = inspect(self)

        if insp.attrs.isOpen.history.has_changes():
            for v in self.myViews:
                v.on_session_isOpen_change()
            for i in self.myImports:
                i.on_session_isOpen_change()
            for e in self.myExports:
                e.on_session_isOpen_change()
                    
    def after_deletion(self):
        for v in self.myViews:
            v.on_session_isOpen_change()
        for i in self.myImports:
            i.on_session_isOpen_change()
        for e in self.myExports:
            e.on_session_isOpen_change()    
        

class Import(Base):
    __tablename__ = 'imports'
    id  = Column(Integer, primary_key=True)
    hid = Column(String)    
    
    #### Parents ####
    mySessionId   : Mapped[int]         = mapped_column(ForeignKey('sessions.id', ondelete="CASCADE"))
    mySession     : Mapped[Session]     = relationship(back_populates = 'myImports') 

    myUserId      : Mapped[str |None]   = mapped_column(ForeignKey('users.id',    ondelete="CASCADE"))
    myUser        : Mapped[User|None]   = relationship(back_populates = 'myImports')

    #### Children ####
    mySpaceId     : Mapped[str]         = mapped_column(ForeignKey('spaces.id'))
    mySpace       : Mapped[Space]       = relationship(back_populates = 'inImports')
        #Spaces are not deleted when an Import is deleted

    #### Data ####
    sessionClosed : Mapped[date|None]   = mapped_column()
    isAlive       : Mapped[bool]        = mapped_column(default = True)
    
    def on_session_isOpen_change():
        
        ...

class Export(Base):
    __tablename__ = 'exports'
    id  = Column(Integer, primary_key=True)
    hid = Column(String)    
    
    #### Parents ####
    mySessionId : Mapped[int]       = mapped_column(ForeignKey('sessions.id', ondelete="CASCADE"))
    mySession   : Mapped[Session]   = relationship(back_populates = 'myExports') 

    myUserId    : Mapped[str |None] = mapped_column(ForeignKey('users.id',    ondelete="CASCADE"))
    myUser      : Mapped[User|None] = relationship(back_populates = 'myExports')
    
    #### Children ####
    mySpaceId   : Mapped[str]       = mapped_column(ForeignKey('spaces.id'))
    mySpace     : Mapped[Space]     = relationship(back_populates = 'inExports')
        #Spaces are not deleted when an export disappears
        
    #### Data ####
    location    : Mapped[str]       = mapped_column()
    onDisk      : Mapped[bool]      = Column(Boolean, default=False)
        #TODO: Tracked Location/s may need to be deleted?
        #TODO: Consider tracking same Exports resulting from multiple sessions? Edge case

    #### TEMP PROPERTY METHODS ####
    marked_for_delete : ClassVar[bool] = False 

    #### Property Methods ####
    @property
    def isAlive(self)->bool:
        i = inspect(self)
        #TODO: i.deleted and i.was_deleted are not showing true after flush where object was deleted?
        return not (i.deleted or i.was_deleted or self.marked_for_delete)

    #### Events ####
    def on_create(self):
        self.mySpace.set_users()
    def on_delete(self):
        print('ON_DELETE HOOK CALLED FOR EXPORT')
        self.marked_for_delete = True
        self.mySpace.set_users()
    def on_session_isOpen_change():    
        ...

class View(Base):
    ''' 
    Blind 'view' (or placeholder) of a namedSpace, untracked, that can be placed on disk. 
    Files being linked to are not guaranteed to exist after session closes, as they are assumed to be transitory (in progress) files.
    Invalidated views 
    '''
    __tablename__ = 'views'
    id  = Column(Integer, primary_key=True)
    hid = Column(String)    

    #### Parents ####
    mySessionId : Mapped[int]          = mapped_column(ForeignKey('sessions.id', ondelete="CASCADE"))
    mySession   : Mapped[Session]      = relationship(back_populates = 'myViews') 

    #### Children ####
    mySpaceId   : Mapped[str|None]     = mapped_column(ForeignKey('spaces.id'))
    mySpace     : Mapped[Space|None]   = relationship(back_populates = 'inViews')
        #Spaces are not deleted when an export disappears

    #### Property Methods ####
    @property
    def isAlive(self)->bool:
        return self.mySession.isOpen and not inspect(self).deleted

    #### Events ####
    def on_create(self):
        self.mySpace.set_users()
    def on_delete(self):
        self.mySpace.set_users()
    def on_session_isOpen_change(self):
        self.mySpace.set_users()

class asc_Space_NamedSpace(Base):
    __tablename__ = 'asc_space_namedspace'
    _use_merge = True

    #### Parents ####
    pSpaceId = mapped_column(String, ForeignKey('spaces.id', ondelete="CASCADE"), primary_key=True)
    pSpace   : Mapped[Space] = relationship(back_populates='mySpaces',foreign_keys=[pSpaceId])
        #Receive cascade to delete self, do **NOT** pass to cSpace (Deletion of named spaces)
    
    #### Children ####
    cName    : Mapped[str]   = mapped_column( primary_key=True)
    cSpaceId : Mapped[str]   = mapped_column( ForeignKey('spaces.id'))
    cSpace   : Mapped[Space] = relationship(back_populates='inSpaces',foreign_keys=[cSpaceId])

    #### Data ####
    hasUsers : Mapped[bool]  = mapped_column(default = True)

    #### Property Methods ####
    def __repr__(self):
        return f"< NamedSpace Object : {self.cName} from space '{self.cSpace.id}' >"


class asc_Space_NamedFile(Base):
    __tablename__ = 'asc_space_namedfile'
    _use_merge = True

    #### Parents ####
    pSpaceId    : Mapped[str]      = mapped_column(ForeignKey('spaces.id', ondelete="CASCADE"), primary_key=True) 
    pSpace      : Mapped[Space]    = relationship(back_populates='myFiles')
        #Receive cascade to delete self, do **NOT** pass to cSpace (Deletion of named files)
    
    #### Children ####
    cName       : Mapped[str]      = mapped_column(primary_key=True)
    cFileId     : Mapped[str|None] = mapped_column(ForeignKey('files.id'))
    cFile       : Mapped[File ]    = relationship(back_populates='inSpaces')

    #### Data ####
    cFileIdCopy : Mapped[str|None] = mapped_column()
    hasUsers    : Mapped[bool]     = mapped_column(default = True)

    #### Property Methods ####
    def __repr__(self):
        return f"< NamedSpace Object : {self.cName} from file '{self.cFile.id}' >"


class Space(Base):
    __tablename__ = 'spaces'
    _use_merge = True
    id  = Column(String, primary_key=True, default=None)

    #### Parents ####
    inSpaces      : Mapped[list[asc_Space_NamedSpace]] = relationship(back_populates="cSpace", foreign_keys=[asc_Space_NamedSpace.cSpaceId])

    inImports     : Mapped[list[Import]]               = relationship(back_populates="mySpace")
    inExports     : Mapped[list[Export]]               = relationship(back_populates="mySpace")
    inViews       : Mapped[list[View]]                 = relationship(back_populates="mySpace")

    #### Children ####
    myFiles       : Mapped[list[asc_Space_NamedFile]]  = relationship(back_populates="pSpace", cascade="all, delete", passive_deletes=True)
    mySpaces      : Mapped[list[asc_Space_NamedSpace]] = relationship(back_populates="pSpace", foreign_keys=[asc_Space_NamedSpace.pSpaceId], cascade="all, delete", passive_deletes=True)
        #Cascade should delete *only* namedSpaces and namedFiles, **Not** actual Spaces|Files.
    
    #### Data ####
    lastHadUser   : Mapped[date|None] = mapped_column(default = None)
    inDecay       : Mapped[bool]      = mapped_column(default = False)
    firstFileDrop : Mapped[date|None] = mapped_column(default = None)

    ### Property Methods ###
    @property
    def hasUsers(self)-> bool:
        print('ANY OF self.inSpaces:',any([x.hasUsers for x in self.inSpaces]))
        print('ANY OF self.inExports:',any([x.isAlive for x in  self.inExports]))
        print('ANY OF self.inImports:',any([x.isAlive for x in  self.inImports]))
        print('ANY OF self.inViews:',any([x.isAlive for x in  self.inViews]))
        return (   any([x.hasUsers for x in self.inSpaces]) 
                or any([x.isAlive  for x in self.inExports]) 
                or any([x.isAlive  for x in self.inImports]) 
                or any([x.isAlive  for x in self.inViews]))


    #### Session Exclusive Data ####
    cached_users  : ClassVar[list[Export|View]] = None

    #### Events ####
    def on_delete(self, safe:bool=True):
        ''' '''
        if safe:
            now = datetime.now()
            assert not self.cached_users is None
            assert len(self.cached_users) == 0
            assert self.lastHadUser
            assert now > self.lastHadUser
            if self.inDecay:
                assert self.firstFileDrop
                assert now > self.firstFileDrop

        for namedSpace in self.inSpaces:
            namedSpace.space.set_decayed()

    #### State Propagation Methods ####
    def set_users(self, chain = None):
        ''' Propagate user count [down] on update '''
        ''' Optimization of not calling recur child on remove user if has any users cannot be done, as may reference it's self  '''
        if chain is None: chain = [self]
        elif self in chain: return

        set_to = self.hasUsers
        print('SET USER VALUE:', set_to)

        for namedFile in self.myFiles:
            namedFile.hasUsers = set_to
            namedFile.cFile.set_users()
        for namedSpace in self.mySpaces:
            namedSpace.hasUsers = set_to
            namedSpace.cSpace.set_users(chain=chain)

        self.enact_user_state()

    def enact_user_state(self):
        ''' Set results of user count observation '''

        if not self.hasUsers:
            if not self.lastHadUser:
                self.lastHadUser = datetime.now()
        else:
            self.lastHadUser = None

    def set_decayed(self):
        ''' [Upward Recursion] Child File (or space) has been deleted, set as Decayed & recur to parents '''
        #Order of operations assertions get_alive_users was called on this object this session
        assert not self.cached_users is None
        assert len(self.cached_users) == 0

        if not self.inDecay:       self.inDecay       = True
        if not self.firstFileDrop: self.firstFileDrop = datetime.now()

        for namedSpace in self.inSpaces:
            namedSpace.pSpace.set_decayed()

    def verify_state(self):
        if self.hasUsers:
            assert not self.lastHadUser
            assert not (self.inDecay or self.firstFileDrop)
        else:
            assert self.lastHadUser
            assert self.inDecay and self.firstFileDrop
    
    #TODO: Re-encorperate [upwards recursion] method of returning users that sets users on the [backswing recursion]
    # def get_alive_users(self, chain=None)->list[Export|View]:
        # ''' [Upward Recursion] Recur through spaces to return 'alive' Exports & Views ('Users' of this space) '''
        # ret = []
        # if chain is None: chain = [self]
        # else: chain.append(self)

        # for namedSpace in self.inSpaces:
        #     if (_space := namedSpace.pSpace) not in chain:
        #         ret.extend(_space.get_alive_users(chain))
        # ret.extend(filter(lambda x: x.isAlive, self.inExports))
        # ret.extend(filter(lambda x: x.isAlive, self.inViews  ))
        # ret = list(set(ret))
        # self.cached_users = ret

        # self.enact_user_count()

        # return ret
        
    # def enact_user_count(self):
        # ''' Set results of user count observation '''

        # if not self.hasUsers:
        #     if not self.lastHadUser:
        #         self.lastHadUser = datetime.now()
        # else:
        #     self.lastHadUser = None

class File(Base):
    __tablename__ = 'files'
    _use_merge = True
    id  = Column(String, primary_key=True)
    hid = Column(String)

    #### Parents ####
    inSpaces    : Mapped[list[asc_Space_NamedFile]] = relationship(back_populates="cFile")

    #### Data ####
    lastHadUser : Mapped[date|None] = mapped_column(default=None)

    #### Property Methods #####
    @property
    def hasUsers(self)-> bool:
        return any([x.hasUsers for x in self.inSpaces])

    ### Unmapped temporary variables ###
    cached_users: ClassVar[list[Export|View]]

    #### Events ####
    def on_delete(self, safe:bool=True):
        ''' Setting decay on parent spaces on deletion and asserting usual situation '''

        if safe:
            now = datetime.now()
            assert not self.cached_users is None
            assert len(self.cached_users) == 0
            assert self.lastHadUser
            assert now > self.lastHadUser

        for namedFile in self.inSpaces:
            namedFile.cFileIdCopy = self.id
            namedFile.pSpace.set_decayed()

    ### State Propigation Methods ###
    def set_users(self):
        if not self.hasUsers:
            if not self.lastHadUser:
                self.lastHadUser = datetime.now()
        else:
            self.lastHadUser = None
    
    #TODO: Re-encorperate [upwards recursion] method of returning users that sets users on the [backswing recursion]
    # def get_alive_users(self):
        # ''' [Upward Recursion] '''
        # ret = []
        # for namedFile in self.inSpaces:
        #     ret.extend(namedFile.pSpace.get_alive_users())
        # ret = list(set(ret))
        # self.cached_users = ret

        # self.enact_user_count()

        # return ret
    
    # def enact_user_count(self):
        # ''' Set results of user count observation '''

        # if not self.hasUsers:
        #     if not self.lastHadUser:
        #         self.lastHadUser = datetime.now()
        # else:
        #     self.lastHadUser = None



#### EVENT HOOKS ####


from sqlalchemy import event


# @event.listens_for(User, 'delete')
@event.listens_for(Export,  'delete')
@event.listens_for(Import,  'delete')
@event.listens_for(Session, 'delete')
def event_start_usercount_update(target, value, oldvalue, initiator):
    ...

@event.listens_for(Export.mySpace,  'set')
@event.listens_for(Import.mySpace,  'set')
@event.listens_for(Session.mySpace, 'set')
def event_start_usercount_update(target, value, oldvalue, initiator):    
    ...

@event.listens_for(Session.isOpen,  'set')
def event_start_usercount_update(target, value, oldvalue, initiator):
    ...

@event.listens_for(File,  'delete')
def event_start_set_decay():
    ...

# @event.listens_for(User.mySessions, 'append')
# def user 
# @event.listens_for(User.myImports,  'append')
# def user 
# @event.listens_for(User.myExports,  'append')
# def user 


# def mount_hooks(sqla_session):
#     ''' Create hooks to propagate complex object states '''

#     @event.listens_for(sqla_session, 'before_flush')
#     def emit_state_changes_before_flush(sqla_session, ctx, instances):

#         for inst in sqla_session.dirty:
#             # if isinstance(inst, (User,Session,Import,Export,View,Space)):
#             if func := getattr(inst,'before_update',None):
#                 func()
#         # sqla_session.set_committed_value()

#     @event.listens_for(sqla_session, 'after_flush')
#     def emit_state_changes_after_flush(sqla_session, ctx):
#         ''' Session handler to emit state changes on deleted objects '''
#         # ''' UNKNOWN: Is the reference still in the relationships?    '''

#         _savepoint = sqla_session.begin_nested()
#         try:
#             for inst in sqla_session.deleted:
#                 # if isinstance(inst, (User,Session,Import,Export,View,Space)):
#                 if func := getattr(inst,'on_delete',None):
#                     func()
#             for inst in sqla_session.new:
#                 # if isinstance(inst, (User,Session,Import,Export,View,Space)):
#                 if func := getattr(inst,'on_create',None):
#                     func()
#             for inst in sqla_session.dirty:
#                 # if isinstance(inst, (User,Session,Import,Export,View,Space)):
#                 if func := getattr(inst,'after_update',None):
#                     func()
#             _savepoint.commit()
#         except:
#             _savepoint.rollback()
#             raise


if __name__ == '__main__':
    Base.metadata.create_all(engine)

    _file  = File( id = 'Random_File_UUID' , hid = 'A_Unique_File' )
    _space = Space(id = 'Random_Space_UUID', hid = 'A_Unique_Space')

    # _asc_Space_NamedFile = asc_Space_NamedFile(pSpaceId =_space, cFileId=_file,cName = 'filename.txt') 
    _asc_Space_NamedFile = asc_Space_NamedFile(cName = 'filename.txt') 
    _asc_Space_NamedFile.pSpace = _space
    _asc_Space_NamedFile.cFile  = _file

    print(_space.myFiles)

    _export = Export(hid = 'MyFirst_Export',location = 'N/a')
    _export.mySpace = _space

    _session = Session(hid='Session1')
    _session.myExports.append(_export)
    # _export.mySession = _session

    _user = User(id = 'Job_Boal', hid='Job_Boal')
    _user.mySessions.append(_session)

    session.add_all([_file,_space,_asc_Space_NamedFile])
    session.commit()
