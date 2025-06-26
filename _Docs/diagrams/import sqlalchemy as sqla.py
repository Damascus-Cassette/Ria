import sqlalchemy as sqla
from sqlalchemy import base as sqlbase



sqla.Table()
    
space_file = sqla.Table('SpaceFile',
    sqla.Column('id'            , sqla.Integer, primary_key=True), #Make UUID?
    sqla.Column('itemName'      , sqla.String),
    sqla.Column('parentSpaceId' , sqla.String, sqla.ForeignKey('spaces.id')),
    sqla.Column('fileId'        , sqla.String, sqla.ForeignKey('files.id') ,backref='asNames'),
)

space_space = sqla.Table('SpaceSpace',
    sqla.Column('id'            , sqla.Integer, primary_key=True), #Make UUID?
    sqla.Column('itemName'      , sqla.String),
    sqla.Column('parentSpaceId' , sqla.String, sqla.ForeignKey('spaces.id')),
    sqla.Column('childSpaceId'  , sqla.String, sqla.ForeignKey('spaces.id'),backref='asNames'),
)

class fm_db_space(sqlbase):
    ''' Container of named files and named sub-spaces '''
    __tablename__ = 'spaces'
    id     = sqla.Column(sqla.String, primary_key = True) #Hash of object

    spaces = sqla.relationship('namedspace', secondary=space_space, backref='pSpace')
    files  = sqla.relationship('namedfile' , secondary=space_file,  backref='pSpace')

    #asNames is backref?
    inSpaces = sqla.relationship('spaces', sqla.ForeignKey('asNames.parentSpaceId') , uselist=True) 

    #inExports
    #inSessions


class fm_db_file(sqlbase):
    ''' Hash as UUID based file entry '''
    __tablename__ = 'files'
    id     = sqla.Column(sqla.String, primary_key = True) #Hash of object
    
    #asNames is backref?
    inSpaces = sqla.relationship('spaces', sqla.ForeignKey('asNames.parentSpaceId') , uselist=True) 


class export(sqlbase):
    __tablename__ = 'exports'
    ''' Holder for exported items, 
    - kept after a session closes 
    - resulting spaces strictly tracked.
    '''

    id        = sqla.Column(sqla.String, primary_key = True)
    hid       = sqla.Column(sqla.String)

    userId    = sqla.relationship('users',    sqla.ForeignKey('users.id')     ,backref='hasExports')
    sessionId = sqla.relationship('sessions', sqla.ForeignKey('session.id')   ,backref='hasExports')
    spaceId   = sqla.relationship('spaces',   sqla.ForeignKey('spaces.id')    ,backref='inExports')

    location  = sqla.Column(sqla.String)
    data      = sqla.Column(sqla.String)

class view(sqlbase):
    __tablename__ = 'views'
    ''' near export duplicate, 
    - used for temporary work spaces           
    - always removed after a session completes 
        - Removes this object, and thus the temp users on the spaces
    - Resulting spaces are not strictly tracked
    '''

    id        = sqla.Column(sqla.String, primary_key = True)
    hid       = sqla.Column(sqla.String)

    userId    = sqla.relationship('users',    sqla.ForeignKey('users.id'))  #,backref='hasViews')
    sessionId = sqla.relationship('sessions', sqla.ForeignKey('session.id')  ,backref='hasViews')
    spaceId   = sqla.relationship('spaces',   sqla.ForeignKey('spaces.id')   ,backref='inViews' )

    location  = sqla.Column(sqla.String)
    data      = sqla.Column(sqla.String)


class session(sqlbase):
    __tablename__ = 'sessions'
    id     = sqla.Column(sqla.String, primary_key = True)
    hid    = sqla.Column()

    isOpen

    views   
    exports 

    perm

    # spaceId   = sqla.relationship('spaces',   sqla.ForeignKey('spaces.id'),  backref='inExports')

class user(sqlbase):
    __tablename__ = 'users'


# class fm_db_interface