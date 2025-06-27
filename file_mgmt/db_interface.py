from sqlalchemy import (Column, ForeignKey, Integer, String, create_engine, Table)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


if __name__ == '__main__':
    db_url = 'sqlite:////database.db'
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

Base = declarative_base()


space_file = Table('SpaceFile',
    Column('id'            , Integer, primary_key=True), #Make UUID?
    Column('itemName'      , String),
    Column('parentSpaceId' , String, ForeignKey('spaces.id')),
    Column('fileId'        , String, ForeignKey('files.id') ,backref='asNames'),
)

space_space = Table('SpaceSpace',
    Column('id'            , Integer, primary_key=True), #Make UUID?
    Column('itemName'      , String),
    Column('parentSpaceId' , String, ForeignKey('spaces.id')),
    Column('childSpaceId'  , String, ForeignKey('spaces.id'),backref='asNames'),
)

class fm_db_space(Base):
    ''' Container of named files and named sub-spaces '''
    __tablename__ = 'spaces'
    id     = Column(String, primary_key = True) #Hash of object

    spaces = relationship('namedspace', secondary=space_space, backref='pSpace')
    files  = relationship('namedfile' , secondary=space_file,  backref='pSpaces')

    inSpaces = relationship('spaces', ForeignKey('asNames.parentSpaceId') , uselist=True) 

    #backref : asNames 
    #backref : inViews
    #backref : inExports
    #backref : inSessions


class fm_db_file(Base):
    ''' Hash as UUID based file entry '''
    __tablename__ = 'files'
    id     = Column(String, primary_key = True) #Hash of object
    
    inSpaces = relationship('spaces', ForeignKey('asNames.parentSpaceId') , uselist=True) 

    #backref : asNames
    #backref : pSpaces

class export(Base):
    __tablename__ = 'exports'
    ''' Holder for exported items, 
    - kept after a session closes 
    - resulting spaces strictly tracked.
    '''

    id        = Column(String, primary_key = True)
    hid       = Column(String)

    userId    = relationship('users',    ForeignKey('users.id')     ,backref='hasExports')
    sessionId = relationship('sessions', ForeignKey('session.id')   ,backref='hasExports')
    spaceId   = relationship('spaces',   ForeignKey('spaces.id')    ,backref='inExports')

    location  = Column(String)
    data      = Column(String)

class view(Base):
    __tablename__ = 'views'
    ''' near export duplicate, 
    - used for temporary work spaces           
    - always removed after a session completes 
        - Removes this object, and thus the temp users on the spaces
    - Resulting spaces are not strictly tracked
    '''

    id        = Column(String, primary_key = True)
    hid       = Column(String)

    userId    = relationship('users',    ForeignKey('users.id'))  #,backref='hasViews')
    sessionId = relationship('sessions', ForeignKey('session.id')  ,backref='hasViews')
    spaceId   = relationship('spaces',   ForeignKey('spaces.id')   ,backref='inViews' )

    location  = Column(String)
    data      = Column(String)


class session(Base):
    __tablename__ = 'sessions'
    id     = Column(String, primary_key = True)
    hid    = Column(String)

    isOpen = Column(Boolean, default=True)

    # backref : hasViews
    # backref : hasExports


class user(Base):
    __tablename__ = 'users'

    id     = Column(String, primary_key = True)
    hid    = Column(String)
    # backref : hasExports
