import sqlalchemy

class fm_db_file():
  @staticmethod
  def _declare_table(db,metadata):
    db.Table('files',metadata,
             db.Column('id', db.String(256), primary_key=True),
             db.Column('spaces', db.ref_list ), #Cross-Table ref, What spaces use this object
             db.Column('users',  db.ref_list ), #Cross-Table ref, What external entities use this object
             db.Column('tags',   db.ref_list ), #Generic Tags on this object
             db.Column('store',  db.String   ), #Storeage location
             db.Column('exts',   db.str_list ), #Valid Extensions
             db.Column('names',  db.str_list ), #List of names this object has been submitted as
             )
  def __init__(self,row:dict):    
    ...

class fm_db_space():
  @staticmethod
  def _declare_table(db,metadata):
    db.Table('spaces',metadata,
             db.Column('id', db.String(256), primary_key=True),
             db.Column('spaces', db.ref_list  ), #Cross-Table ref, What spaces are in this object
             db.Column('files' , db.ref_list  ), #Cross-Table ref, What Files  are in this object
             db.Column('users',  db.ref_list  ), #Cross-Table ref, What external entities use this object
             db.Column('tags',   db.ref_list  ), #Generic Tags on this object
             db.Column('store',  db.String    ), #Storeage location
             db.Column('names',  db.str_list  ), #List of names this object has been submitted as
             )
  def __init__(self,row:dict):
    ...
    
class fm_db_user():
  @staticmethod
  def _declare_table(db,metadata):
    db.Table('users',metadata,
             db.Column('id',  db.String(256)   , primary_key=True),
             db.Column('hid', db.String(256))  ,
             db.Column('last_use', db.Datetime),
            )
  def __init__(self,row:dict):
    ...

class fm_db_tag():
  @staticmethod
  def _declare_table(db,metadata):
    db.Table('users',metadata,
             db.Column('id',    db.String(256) , primary_key=True),
             db.Column('value', db.String(256)),
            )
  def __init__(self,row:dict):
    ...
  
class fm_db_struct_file():
  #Defines storage locations & version.
  export_loc : str
  ... #TODO: Define the rest


class fm_db_interface():
  ''' Exists within the host, '''
  file  : fm_db_file
  space : fm_db_space
  coll  : fm_db_collection

  def __init__(db_loc,file_loc):
    # Intialize, provide root file w/ cached data?
    # Cached file is defines storage struct
    ...

  def ensure_table():
    ...
  
