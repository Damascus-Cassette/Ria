import sqlalchemy as sqla
from sqlalchemy import base as sqlbase



class fm_db_file(sqlbase):
    ''' Hash as UUID based file entry '''
    __tablename__ = 'files'
    id     = sqla.Column(primary_key = True)
    #names
    spaces = sqla.relationship('spaces',uselist=True,backref='spaces')
    
class fm_db_space(sqlbase):
    ''' Container of named files and named sub-spaces '''
    __tablename__ = 'spaces'
    id     = sqla.Column(primary_key = True)
    #names
    spaces = sqla.relationship('namedspace',uselist=True,backref='spaces')
    files  = sqla.relationship('namedfile' ,uselist=True,backref='files')
    

class rel_namedfile():
    __tablename__ = 'namedfile'
    space_user = 
    name   = sqla.Column(sqla.String)    
    target = sqla.relationship('files' ,backref='names')

class rel_namedspace():
    __tablename__ = 'namedspace'
    target = sqla.relationship('spaces',backref='names')    
    name   = sqla.Column(sqla.String)    
    



class fm_db_user(sqlbase):
    ...
class fm_db_tag(sqlbase):
    ...
class fm_db_struct_file(sqlbase):
    ...
# class fm_db_interface