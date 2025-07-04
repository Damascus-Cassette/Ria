from __future__ import annotations
from sqlalchemy import (Column, Boolean, ForeignKey, Integer, String, create_engine, Table)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Mapped, mapped_column


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
    mySessions: Mapped[list[Session]] = relationship(back_populates='myUser')
    myExports : Mapped[list[Export]]  = relationship(back_populates='myUser')


class Session(Base):
    __tablename__ = 'sessions'
    id  = Column(Integer, primary_key=True)
    hid = Column(String)    

    isOpen : Mapped[bool] = mapped_column(default=True)

    myExports: Mapped[list[Export]] = relationship(back_populates='mySession')
    myViews:   Mapped[list[View]]   = relationship(back_populates='mySession')
    
    myUserId : Mapped[str]  = mapped_column(ForeignKey('users.id'))
    myUser   : Mapped[User] = relationship(back_populates='mySessions')


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


class Space(Base):
    __tablename__ = 'spaces'
    _use_merge = True
    id  = Column(String, primary_key=True, default=None)

    myFiles  : Mapped[list[asc_Space_NamedFile]]  = relationship(back_populates="pSpace")
    mySpaces : Mapped[list[asc_Space_NamedSpace]] = relationship(back_populates="pSpace", foreign_keys=[asc_Space_NamedSpace.pSpaceId])
    inSpaces : Mapped[list[asc_Space_NamedSpace]] = relationship(back_populates="cSpace", foreign_keys=[asc_Space_NamedSpace.cSpaceId])

    inExports : Mapped[list[Export]]              = relationship(back_populates="mySpace")
    inViews   : Mapped[list[View]]                = relationship(back_populates="mySpace")

class asc_Space_NamedSpace(Base):
    __tablename__ = 'asc_space_namedspace'
    _use_merge = True

    pSpaceId = mapped_column(String, ForeignKey('spaces.id'), primary_key=True)  
    cName    = mapped_column(String                         , primary_key=True)
    cSpaceId = mapped_column(String, ForeignKey('spaces.id' ,)                )
    
    pSpace : Mapped[Space] = relationship(back_populates='mySpaces',foreign_keys=[pSpaceId])
    cSpace : Mapped[Space] = relationship(back_populates='inSpaces',foreign_keys=[cSpaceId])

    def __repr__(self):
        return f"< NamedSpace Object : {self.cName} from space '{self.cSpace.id}' >"


class File(Base):
    __tablename__ = 'files'
    _use_merge = True
    id  = Column(String, primary_key=True)
    hid = Column(String)

    inSpaces : Mapped[list[asc_Space_NamedFile]] = relationship(back_populates="cFile")


class asc_Space_NamedFile(Base):
    __tablename__ = 'asc_space_namedfile'
    _use_merge = True

    pSpaceId    : Mapped[str]      = mapped_column(ForeignKey('spaces.id'), primary_key=True) 
    cName       : Mapped[str]      = mapped_column(primary_key=True)

    cFileId     : Mapped[str|None] = mapped_column(ForeignKey('files.id'))
    cFileIdCopy : Mapped[str|None] = mapped_column()

    pSpace : Mapped[Space] = relationship(back_populates='myFiles')
    cFile  : Mapped[File ] = relationship(back_populates='inSpaces')

    def __repr__(self):
        return f"< NamedSpace Object : {self.cName} from file '{self.cFile.id}' >"




    



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

    #TODO: Consider better primary_key s being spaceId & location?
    #TODO: Consider tracking same Exports resulting from multiple sessions? Edge case







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
