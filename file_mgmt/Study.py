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

    pSpaceId = mapped_column(String, ForeignKey('spaces.id'), primary_key=True) 
    cName    = mapped_column(String                         , primary_key=True)
    cFileId  = mapped_column(String, ForeignKey('files.id')                   )
        # The same file can exist multiple times in the same space, but only under different names
        # But multiple files cannot exist in the space space with the same name. 
        # TODO: Consider/Research how to enforce a unique key constraint for space-> file:name via sqla

    pSpace : Mapped[Space] = relationship(back_populates='myFiles')
    cFile  : Mapped[File ] = relationship(back_populates='inSpaces')

    def __repr__(self):
        return f"< NamedSpace Object : {self.cName} from file '{self.cFile.id}' >"

class asc_Space_NamedSpace(Base):
    __tablename__ = 'asc_space_namedspace'

    pSpaceId = mapped_column(String, ForeignKey('spaces.id'), primary_key=True)  
    cName    = mapped_column(String                         , primary_key=True)
    cSpaceId = mapped_column(String, ForeignKey('spaces.id')                  )
    
    pSpace : Mapped[Space] = relationship(back_populates='mySpaces',foreign_keys=[pSpaceId])
    cSpace : Mapped[Space] = relationship(back_populates='inSpaces',foreign_keys=[cSpaceId])

    #Untested assumption: via primary_merge pSpaceId & pSpace are asociated and are left_column, and via secondary_merge cSpaceId & cSpace are asc and right_column

    def __repr__(self):
        return f"< NamedSpace Object : {self.cName} from space '{self.cSpace.id}' >"

class File(Base):
    __tablename__ = 'files'
    id  = Column(String, primary_key=True)
    hid = Column(String)
    inSpaces : Mapped[list[asc_Space_NamedFile]] = relationship(back_populates="cFile")
    # TODO: AsociationProxy Object

class Space(Base):
    __tablename__ = 'spaces'
    id  = Column(String, primary_key=True)
    hid = Column(String)    
    
    myFiles  : Mapped[list[asc_Space_NamedFile]] = relationship(back_populates="pSpace")
    
    mySpaces : Mapped[list[asc_Space_NamedSpace]] = relationship(back_populates="pSpace", foreign_keys=[asc_Space_NamedSpace.pSpaceId])
    inSpaces : Mapped[list[asc_Space_NamedSpace]] = relationship(back_populates="cSpace", foreign_keys=[asc_Space_NamedSpace.cSpaceId]) 
        #foreign keys also available as str, but since it's eval it must include list, ie foreign_keys='[asc_Space_NamedSpace.cSpaceId]'
        #this is since there are multiple keys asociated with the same relationship class target

    # TODO: AsociationProxy Objects for myFiles and mySpaces, replace current with myNamedSpaces and myNamedFiles
    inExports : Mapped[list[Export]]             = relationship(back_populates="mySpace")



class Export(Base):
    __tablename__ = 'exports'
    id  = Column(Integer, primary_key=True)
    hid = Column(String)    
    
    mySpaceId : Mapped[String]  = mapped_column(ForeignKey('spaces.id'))
    mySpace   : Mapped[Space]   = relationship(back_populates='inExports')

    location  : Mapped[String]  = mapped_column()

    #TODO: Consider better primary_key s being spaceId & location?

Base.metadata.create_all(engine)

if __name__ == '__main__':

    _file  = File( id = 'Random_File_UUID' , hid = 'A_Unique_File' )
    _space = Space(id = 'Random_Space_UUID', hid = 'A_Unique_Space')

    # _asc_Space_NamedFile = asc_Space_NamedFile(pSpaceId =_space, cFileId=_file,cName = 'filename.txt') 
    _asc_Space_NamedFile = asc_Space_NamedFile(cName = 'filename.txt') 
    _asc_Space_NamedFile.pSpace = _space
    _asc_Space_NamedFile.cFile  = _file

    print(_space.myFiles)

    _export = Export(hid = 'MyFirst_Export')
    _export.mySpace = _space

    session.add_all([_file,_space,_asc_Space_NamedFile])
    session.commit()
