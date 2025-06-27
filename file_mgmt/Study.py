from sqlalchemy import (Column, Boolean, ForeignKey, Integer, String, create_engine, Table)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


if __name__ == '__main__':
    db_url = 'sqlite:///database.db'
    engine  = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

Base = declarative_base()


class rel_SpaceFile(Base):
    __tablename__ = 'rel_spacefile'
    id  = Column(Integer, primary_key=True)

    pSpaceId = Column(String, ForeignKey('spaces.id')) 
    cFileId  = Column(String, ForeignKey('files.id') )


class Space(Base):
    __tablename__ = 'spaces'
    id  = Column(String, primary_key=True)
    hid = Column(String)    

    myFiles = relationship("File", secondary='rel_spacefile', back_populates="inSpaces")
        #First arg is the class name
        #secondary means routing via a relationship table, allowing for many<->many relationships
        #backpopulates refers to an explicit value to update on the target obj in the table

class File(Base):
    __tablename__ = 'files'
    id  = Column(String, primary_key=True)
    hid = Column(String)

    inSpaces = relationship("Space", secondary='rel_spacefile', back_populates="myFiles")


Base.metadata.create_all(engine)

if __name__ == '__main__':

    _file  = File( id = 'Random_File_UUID' , hid = 'A_Unique_File' )
    _space = Space(id = 'Random_Space_UUID', hid = 'A_Unique_Space')

    # _rel_SpaceFile = rel_SpaceFile(pSpaceId =_space, cFileId=_file) 
    _file.inSpaces.append(_space)

    print(_space.myFiles)

    session.add_all([_file,_space])
    session.commit()
