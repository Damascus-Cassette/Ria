from __future__ import annotations
from sqlalchemy import (Column, Boolean, ForeignKey, Integer, String, create_engine, Table)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Mapped, mapped_column


if __name__ == '__main__':
    db_url = 'sqlite:///database.db'
    engine  = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

Base = declarative_base()


class rel_Space_NamedFile(Base):
    __tablename__ = 'rel_space_namedfile'

    pSpaceId = mapped_column(String, ForeignKey('spaces.id'), primary_key=True) 
    cName    = mapped_column(String                         , primary_key=True)
    cFileId  = mapped_column(String, ForeignKey('files.id')                   )
        # The same file can exist multiple times in the same space, but only under different names
        # But multiple files cannot exist in the space space with the same name. 
        # TODO: Consider/Research how to enforce a unique key constraint for space-> file:name via sqla

    pSpace : Mapped[Space] = relationship(back_populates='myFiles')
    cFile  : Mapped[File ] = relationship(back_populates='inSpaces')

class Space(Base):
    __tablename__ = 'spaces'
    id  = Column(String, primary_key=True)
    hid = Column(String)    
    myFiles : Mapped[list[rel_Space_NamedFile]] = relationship(back_populates="pSpace")

class File(Base):
    __tablename__ = 'files'
    id  = Column(String, primary_key=True)
    hid = Column(String)
    inSpaces : Mapped[list[rel_Space_NamedFile]] = relationship(back_populates="cFile")


Base.metadata.create_all(engine)

if __name__ == '__main__':

    _file  = File( id = 'Random_File_UUID' , hid = 'A_Unique_File' )
    _space = Space(id = 'Random_Space_UUID', hid = 'A_Unique_Space')

    # _rel_Space_NamedFile = rel_Space_NamedFile(pSpaceId =_space, cFileId=_file,cName = 'filename.txt') 
    _rel_Space_NamedFile = rel_Space_NamedFile(cName = 'filename.txt') 
    _rel_Space_NamedFile.pSpace = _space
    _rel_Space_NamedFile.cFile  = _file

    print(_space.myFiles)

    session.add_all([_file,_space,_rel_Space_NamedFile])
    session.commit()
