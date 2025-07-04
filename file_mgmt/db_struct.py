from __future__ import annotations
from sqlalchemy import (Column, Boolean, ForeignKey, Integer, String, create_engine, Table)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Mapped, mapped_column


if __name__ == '__main__':
    db_url = 'sqlite:///database.db'
    engine  = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

Base = declarative_base()

class asc_Space_NamedFile(Base):
    __tablename__ = 'asc_space_namedfile'
    _use_merge = True

    pSpaceId    : Mapped[str]      = mapped_column(ForeignKey('spaces.id'), primary_key=True) 
    cName       : Mapped[str]      = mapped_column(primary_key=True)
    cFileId     : Mapped[str|None] = mapped_column(ForeignKey('files.id'))
    cFileIdCopy : Mapped[str]      = mapped_column()
    
    def copy_key(self):
        ''' Copy key incase cFileId 'Decays'/is removed from the db '''
        if self.cFileId:
            self.cFileIdCopy = self.cFileId

    pSpace : Mapped[Space] = relationship(back_populates='myFiles')
    cFile  : Mapped[File ] = relationship(back_populates='inSpaces')


        # The same file can exist multiple times in the same space, but only under different names
        # But multiple files cannot exist in the space space with the same name. 
        # TODO: Consider/Research how to enforce a unique key constraint for space-> file:name via sqla

    def __repr__(self):
        return f"< NamedSpace Object : {self.cName} from file '{self.cFile.id}' >"

class asc_Space_NamedSpace(Base):
    __tablename__ = 'asc_space_namedspace'
    _use_merge = True

    pSpaceId = mapped_column(String, ForeignKey('spaces.id'), primary_key=True)  
    cName    = mapped_column(String                         , primary_key=True)
    cSpaceId = mapped_column(String, ForeignKey('spaces.id' ,)                )
    
    pSpace : Mapped[Space] = relationship(back_populates='mySpaces',foreign_keys=[pSpaceId])
    cSpace : Mapped[Space] = relationship(back_populates='inSpaces',foreign_keys=[cSpaceId])

    #Untested assumption: via primary_merge pSpaceId & pSpace are asociated and are left_column, and via secondary_merge cSpaceId & cSpace are asc and right_column

    def __repr__(self):
        return f"< NamedSpace Object : {self.cName} from space '{self.cSpace.id}' >"

class File(Base):
    #User count is only for 'alive' parents of this
    #Recurses in spaces.
    __tablename__ = 'files'
    _use_merge = True
    id  = Column(String, primary_key=True)
    hid = Column(String)
    inSpaces : Mapped[list[asc_Space_NamedFile]] = relationship(back_populates="cFile")
    # TODO: AsociationProxy Object

    def _refs(self,alive=True)->list:
        view_users    = []
        session_users = []
        export_users  = []
        for nFile in self.inSpaces:
            space = nFile.space
            view_users.extend(space._refs_view(alive=True))
            session_users.extend(space._refs_session(alive=True))
            export_users.extend(space._refs_export(alive=True))
        return set(view_users) , set(session_users) , set(export_users)
        
class Space(Base):
    __tablename__ = 'spaces'
    _use_merge = True
    id  = Column(String, primary_key=True, default=None)

    isDecayed : Mapped[bool] = mapped_column()  
        #Shouldn't be primary key, as this is an existing unique space, just without all it's files
        #Set to true when a file is removed from the database before the space is.
    isDecayOrigSpaceID : Mapped[Space|None] = mapped_column(ForeignKey('spaces.id')) 
        #This is if the file is a snapshot of a decayed space

    myFiles  : Mapped[list[asc_Space_NamedFile]]  = relationship(back_populates="pSpace")
    mySpaces : Mapped[list[asc_Space_NamedSpace]] = relationship(back_populates="pSpace", foreign_keys=[asc_Space_NamedSpace.pSpaceId])
    inSpaces : Mapped[list[asc_Space_NamedSpace]] = relationship(back_populates="cSpace", foreign_keys=[asc_Space_NamedSpace.cSpaceId]) 
        #foreign keys also available as str, but since it's eval it must include list, ie foreign_keys='[asc_Space_NamedSpace.cSpaceId]'
        #this is since there are multiple keys asociated with the same relationship class target

    inExports : Mapped[list[Export]]          = relationship(back_populates="mySpace")
    # inViews : Mapped[list[views]]             = relationship(back_populates="mySpace")
    

    def _refs_session(self,open=None,alive=True,chain=None) -> list[Session]:
        if chain is None: chain = [self]
        elif self in chain: return []
        ret :list[Session] = []
        for export in self._refs_export(alive=alive):
            ret.append(export.mySession)
        if open is True:
            ret = filter(ret,lambda x: x.isOpen)
        elif open is False:
            ret = filter(ret,lambda x: not x.isOpen)
        return list(set(ret))

    def _refs_export(self,alive=True,chain=None)->list[Export]:
        if chain is None: chain = [self]
        elif self in chain: return []
        ret = []
        for space in self.inSpaces: 
            ret.extend(space._refs_export(alive=alive,chain=chain))
        if alive:
            ret = filter(self.inExports,lambda x: x.alive)
        elif alive is False:
            ret = filter(self.inExports,lambda x: not x.alive)
        else:
            ret.extend(self.inExports)
        return list(set(ret))
        
    def _refs_view(self,alive=True,chain=None):
        if chain is None: chain = [self]
        elif self in chain: return []
        ret = []
        for space in self.inSpaces: 
            ret.extend(space._refs_export(alive=alive,chain=chain))
        if alive:
            ret = filter(self.inViews,lambda x: x.alive)
        elif alive is False:
            ret = filter(self.inViews,lambda x: not x.alive)
        else:
            ret.extend(self.inViews)
        return list(set(ret))

class Export(Base):
    __tablename__ = 'exports'
    id  = Column(Integer, primary_key=True)
    hid = Column(String)    
    
    mySpaceId   : Mapped[str]  = mapped_column(ForeignKey('spaces.id'))
    mySpace     : Mapped[Space]   = relationship(back_populates='inExports')

    location    : Mapped[str]  = mapped_column()

    mySessionId : Mapped[int]     = mapped_column(ForeignKey('sessions.id'))
    mySession   : Mapped[Session] = relationship(back_populates = 'myExports') 

    myUserId    : Mapped[str |None] = mapped_column(ForeignKey('users.id'))
    myUser      : Mapped[User|None] = relationship(back_populates='myExports')

    onDisk      : Mapped[bool] = Column(Boolean, default=False)

    #TODO: Consider better primary_key s being spaceId & location?
    #TODO: Consider tracking same Exports resulting from multiple sessions? Edge case

    @property
    def alive(self):
        return self.mySession or self.myUser

class View(Base):
    ''' 
    Blind 'view' (or placeholder) of a namedSpace, untracked, that can be placed on disk. 
    Files being linked to are not guaranteed to exist after session closes, as they are assumed to be transitory (in progress) files.
    Invalidated views 
    '''

    __tablename__ = 'views'
    id  = Column(Integer, primary_key=True)
    hid = Column(String)    
    
    mySpaceId   : Mapped[str|None]     = mapped_column(ForeignKey('spaces.id'))
    mySpace     : Mapped[Space|None]   = relationship(back_populates='inViews')

    mySessionId : Mapped[int]     = mapped_column(ForeignKey('sessions.id'))
    mySession   : Mapped[Session] = relationship(back_populates = 'myViews') 

    @property
    def decayed_state()->bool:
        #Check if the file/space has been cleaned.
        #If so, this view is decayed and would need to be re-generated.
        ...

    # location    : Mapped[str]  = mapped_column()
    # onDisk      : Mapped[bool] = Column(default =False)
    # onDiskHash  : Mapped[str]  = Column(default ='')
        #Can be used as an indicator of decay of View
        #Use onDiskHash from the files's metadata (create time,edit time, byte size) to check if it's changed

    #TODO: Consider better primary_key s being spaceId & location?
    #TODO: Consider tracking same Exports resulting from multiple sessions? Edge case

    @property
    def alive(self):
        return self.mySession or self.myUser

class Session(Base):
    __tablename__ = 'sessions'
    id  = Column(Integer, primary_key=True)
    hid = Column(String)    

    isOpen : Mapped[bool] = mapped_column(default=True)

    myExports: Mapped[list[Export]] = relationship(back_populates='mySession')
    myViews:   Mapped[list[View]]   = relationship(back_populates='mySession')
    
    myUserId : Mapped[str]  = mapped_column(ForeignKey('users.id'))
    myUser   : Mapped[User] = relationship(back_populates='mySessions')

    @property
    def alive(self):
        return True

class User(Base):
    __tablename__ = 'users'
    id  = Column(String, primary_key=True)
    hid = Column(String)    
    mySessions: Mapped[list[Session]] = relationship(back_populates='myUser')
    myExports : Mapped[list[Export]]  = relationship(back_populates='myUser')



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
