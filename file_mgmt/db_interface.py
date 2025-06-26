class fm_sql_file():
  ''' Object initilized from sqlite row, Also defines row '''
  _key_col  = ''
  _collumns = {
    '':list[]
  }
  def __init__(self,row:dict):    
    ...

class fm_sql_space():
  ''' Object initilized from sqlite row '''
  def __init__():
    ...

class fm_sql_interface():
  ''' Exists within the a symlink approved entity '''
  file  : fm_sql_file
  space : fm_sql_space
  coll  : fm_sql_collection

  def __init__(file_loc):
    ...

  def ensure_table():
    ...
  
