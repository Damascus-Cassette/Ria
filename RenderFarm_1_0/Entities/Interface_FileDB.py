from fastapi                           import (Request, Response, APIRouter, WebSocket as WebSocketManager, UploadFile, Form, File as fapi_File)
from fastapi.responses                 import FileResponse, HTMLResponse
# from starlette.websockets              import WebSocketDisconnect as WebSocketDisconnect_M 
# from ws4py.client.threadedclient       import WebSocketClient 

from .EventSystem.Struct_Pub_Sub_v1_2  import Event_Router
from ..Web_Interface.API_V1_8          import (Foreign_Entity_Base, Local_Entity_Base, Interface_Base, IO)
from ..Web_Interface.Websocket_Pool    import Manager_Websocket_Wrapper_Simul_Default

from .Websocket_Messsage                        import make_message, intake_message
from .Statics                          import Message_Topics, Admin_Message_Actions, FILEDB_Message_Actions, FILEDB_Message_Tables

from .FileDB.db_repo_V1_1              import file_utils
from .FileDB.db_struct                 import User,Session,Import,Export,View,asc_Space_NamedSpace,asc_Space_NamedFile,Space,File
from .FileDB.FileHashing               import uuid_utils, file_utils as _file_utils

from functools  import partial
from typing     import TypeAlias

import asyncio


AnyTableType : TypeAlias = User|Session|Import|Export|View|asc_Space_NamedSpace|asc_Space_NamedFile|Space|File

class _transaction():
    ''' Placeholder for future complex use. I dont remember exactly why I wanted this before'''
    def __init__(self,func,filter=None):
        self.func   = func
        self.filter = filter

    def __get__(self,inst,inst_cls):
        if inst is None:
            return self
        return partial(self, inst)
    
    def __call__(self, inst, target_row, *args, **kwargs):
        #Handle database commit and roleback here if not nested iirc
        if self.filter:
            if not self.filter(target_row.__class__):
                raise TypeError(f'TARGET ROW DID NOT PASS {self.func.__name__} TRANSACTION FILTER: {target_row.__class__}')
        return self.func(inst, *args, **kwargs)

    @classmethod
    def _wrapper(cls):
        def wrapper(func):
            return cls(func)
        return wrapper
    
transaction = _transaction._wrapper

from contextlib  import contextmanager
from contextvars import ContextVar

file_utils      : _file_utils = ContextVar('active_file_utilities_inst', default= None)
Active_Session                = ContextVar('active_file_db_session',default = None)

@contextmanager
def Active_file_utils_As(utils:_file_utils):
    t = file_utils.set(utils)
    yield
    file_utils.reset(t)    

@contextmanager
def Active_Session_As(engine):
    t = Active_Session.set(engine)
    yield
    Active_Session.reset(t)    

@contextmanager
def set_context(local_e):
    with Active_Session_As(local_e.get_file_db_session), Active_file_utils_As(local_e.settings.FileDBSettings.fileutils):
        yield


class _header_interface():
    def _update(self,table,row_item,data:dict):
        for k,v in data.items():
            if k in table._ext_allowable_:
                setattr(row_item,k)
            else:
                raise KeyError(f'K:V {k}:{v} IS NOT ALLOWED TO BE SET ON {table}')

    def find[T:AnyTableType](self, table:T, item_id:str)->T:  #Get
        return Active_Session.get().query(table).first(id=item_id)

    def query(self,table, **defintions):  #Get
        return Active_Session.get().query(table).all(**defintions)

    def _create_view(self, table, session_id:str, data:dict):
        target_session = self.find(Session, session_id)
        assert target_session is not None
        new = table()
        new.mySession = target_session
        self._update(data)
        return new

    def _create_import_export(self, table, user_id:int, session_id:int, data:dict):
        target_session = self.find(Session, session_id)
        target_user    = self.find(User, user_id)
        assert target_session is not None
        assert target_user    is not None
        new = table()
        new.mySession = target_session
        new.myUser    = target_user
        self._update(data)
        return new

    def _create_session(self, table, user_id:int, data:dict):
        target_user = self.find(User, user_id)
        assert target_user is not None
        new = table()
        new.myUser    = target_user
        self._update(data)
        return new

    def _create_generic(self, table, data:dict):
        new = table()
        self._update(data)
        return new
    

    @transaction()
    def create(self, table, **payload): #Post 
        if   table is Import:
            val = self._create_import_export(table,**payload)
        elif table is Export:
            val = self._create_import_export(table,**payload)
        elif table is View:
            val = self._create_view(table,**payload)
        elif table is Session:
            val = self._create_session(table,**payload)
        else:
            val = self._create_generic(table,**payload)
        Active_Session.get().append(val)
        return val
    
    @transaction()
    def update(self, table, target_row, **payload): #Patch
        self._update(target_row,payload)
    
    @transaction()
    def delete(self, table, target_row, **payload): #Delete
        Active_Session.get().remove(target_row)

    def diff(self, table, mode:str, object_def:dict)->bool:
        ''' Treat {key : (_Any,(value_series,...))} as an operation to parse '''
        ...

    def data(self, table, target_row):
        ...



    #SESSION
    @transaction(filter = lambda x: x is Session)
    def open(self, table, target_row):
        target_row.isOpen = True

    @transaction(filter = lambda x: x is Session)
    def close(self, table, target_row):
        target_row.isFalse = True


    #VIEW | IMPORT | EXPORT | NAMEDSPACE | NAMEDFILE -> SPACE | FILE

    @transaction(filter = lambda x: x in [Import,Export,View,asc_Space_NamedSpace,asc_Space_NamedFile,Space,File])
    def expose(self, table, target_row, **payload): 
        raise NotImplementedError('TODO: PORT FROM ORIGINAL')

    def cleanup(self, table, target_row, **payload): 
        raise NotImplementedError('Settup Intial routine first!')


    #VIEW | IMPORT | EXPORT | NAMEDSPACE | NAMEDFILE -> SPACE
    # @transaction(filter = lambda x: x in [Import,Export,View,asc_Space_NamedSpace,asc_Space_NamedFile,Space,File])

    def diff_future(self, files:list[str], spaces:list[str])->list: #get
        ''' Determine elements that need to be uploaded by hash diff'''
        elem:dict
        need_hashes  = []
        for elem in files:
            if self.find(File ,elem['data_hash']) is None:
                need_hashes.append(elem['data_hash'])
        for elem in spaces:
            if self.find(Space,elem['data_hash']) is None:
                need_hashes.append(elem['data_hash'])
        return need_hashes

    @transaction()
    def create_named_file_from_structure(self,structure:dict):
        if (nspace:=self.find(File, structure['full_hash'])) is not None: return nspace
        nfile = asc_Space_NamedFile()

        if (file:=self.find(File,structure['data_hash'])) is None:
            raise Exception('FILE DOES NOT EXIST ON DB! Delayed upload not yet supported!!:',structure['data_hash'], 'of', structure)
            
        nspace.cFile = file
        return nspace

    @transaction()
    def create_named_space_from_structure(self,structure:dict)->asc_Space_NamedSpace:
        if (nspace:=self.find(structure['full_hash'])) is not None: return nspace
        nspace = asc_Space_NamedSpace()

        if (space:=self.find(structure['data_hash'])) is None:
            space = self.create_space_from_structure(structure)
        nspace.cSpace = space
        return nspace

    @transaction()
    def create_space_from_structure(self, structure):
        ''' Requires that all files to already be uploaded !!! '''
        file_children  = []
        space_children = []

        if (space:=self.find(Space, structure['data_hash'])) is not None: return space

        space = Space()
        for elem_data in structure['children']:
            if elem_data['_type']   == 'NAMEDFILE':
                space.myFiles.append(self.create_named_file_from_structure(elem_data))

            elif elem_data['_type'] == 'NAMEDSPACE':
                space.mySpaces.self.space_children.append(self.create_named_space_from_structure(elem_data))
            
            else: raise Exception(f'DONT RECOGNIZE TYPE: {elem_data["_type"]}')
        
        space.id = structure['data_hash']
        
        return space
    
    @transaction()
    async def upload_file(self, file:UploadFile|bytearray, metadata:dict={})->File:

        if data_hash:=metadata.get('data_hash'):
            if filerow:=self.find(File,data_hash):
                if fp:=file_utils.get().file_on_server(filerow):
                    print(f'WARNING! FILE WITH DATA_HASH {data_hash} ALREADY UPLOADED AND ON DISC AT {fp}, DUMPING AND RETURING ON_DISC')
                    if isinstance(file, UploadFile): await file.close()
                    return filerow
        
        if isinstance(file, UploadFile): data_hash = uuid_utils.get_bytearray_hash(file.file)
        else:                            data_hash = uuid_utils.get_bytearray_hash(file)
        
        if _mdata_hash:= metadata.get('data_hash',None):
            if data_hash != _mdata_hash:
                print(f'MANAGER DID NOT GET THE SAME BYTE HASH:',data_hash,  metadata['data_hash'], metadata)
                

        if (filerow:=self.find(File,data_hash)) is None: filerow = File()
        elif fp:=file_utils.get().file_on_server(filerow): 
            if isinstance(file, UploadFile): await file.close()
            print(f'WARNING! FILE WITH DATA_HASH {data_hash} ALREADY UPLOADED AND ON DISC AT {fp}, DUMPING AND RETURING ON_DISC')
            return filerow
        
        if isinstance(file, UploadFile):
            await file_utils.get().dump_bytearray(file.file, data_hash=data_hash)
            await file.close()
        else:
            await file_utils.get().dump_bytearray(file,      data_hash=data_hash)

        filerow.id = data_hash

        return filerow
    
    # def upload_import_export(self, table, space_id, session_id, user_id, **container_data,):
    #     container = self._create_import_export(table, session_id, user_id, container_data)
    #     container.mySpaceId = space_id
    #     Active_Session.get().append(container)

    # def upload_view(self, table, space_id, session_id, **container_data):
    #     container = self._create_import_export(table, session_id, container_data)
    #     container.mySpaceId = space_id
    #     Active_Session.get().append(container)
        
    
    @transaction(filter = lambda x: x in [Import,Export,View,asc_Space_NamedSpace,asc_Space_NamedFile,Space,File])
    def upload(self,table, **payload): #Put
        #CASE: VIEW | IMPORT | EXPORT | NAMEDSPACE | NAMEDFILE: Create and then upload to container entity types
        if   table is File:
            self.upload_file(**payload)
        elif table is Space:
            self.upload_space(**payload)
        elif table is asc_Space_NamedFile:
            self.upload_named_file(**payload)
        elif table is asc_Space_NamedSpace:
            self.upload_named_space(**payload)
        elif table in [Import,Export,View]:
            self.upload_import_export_view(**payload)
        

    def download(self,table, **payload)->bytearray|tuple[bytearray]: #get
        #CASE: VIEW | IMPORT | EXPORT  : Download space via compressed folder  
        #CASE: NAMEDSPACE | NAMEDFILE  : Download file named
        raise Exception('TRYING HERE')

header_interface = _header_interface()


    
class _generic_filedb_interface(Interface_Base):
    Base   : None
    router = APIRouter()       

    #ALL:
    # @IO.Get(router,'/raw_table')
    # def raw_data(self, local_e, foreign_e, req_or_ws, uid):  #Get
    #     with set_context(local_e):
    #         self.parent.TableType._template_id #DEFER: Links to other tables by type? Websocket stream tables?

    # @IO.Get(router,'/raw_data/{uid}')
    # def raw_data(self, local_e, foreign_e, req_or_ws, uid):  #Get
    #     with set_context(local_e):
    #         return  header_interface.find(self.parent.TableType, uid)._as_link_dict() #DEFER: Links to other tables by type?

    @IO.Get(router,'/query')
    def query(self, local_e, foreign_e, req_or_ws, **payload):  #Get
        with set_context(local_e):
            return [x.uid for x in header_interface.query(self.parent.TableType,**payload)]
    
    @IO.Get(router,'/find')
    def find(self, local_e, foreign_e, req_or_ws, **payload):  #Get
        with set_context(local_e):
            return header_interface.find(self.parent.TableType, **payload).uid

    @IO.Get(router,'/table')
    def data(self, local_e, foreign_e, req_or_ws, **payload):  #Get
        with set_context(local_e):
            return header_interface.data(self.parent.TableType, **payload)

    @IO.Post(router,'/table')
    def create(self, local_e, foreign_e, req_or_ws, **payload): #Post
        with set_context(local_e):
            return header_interface.create(self.parent.TableType, **payload)

    @IO.Patch(router,'/table')
    def update(self, local_e, foreign_e, req_or_ws, **payload): #Patch
        with set_context(local_e):
            return header_interface.update(self.parent.TableType, **payload)

    @IO.Delete(router,'/table')
    def delete(self, local_e, foreign_e, req_or_ws, **payload): #Delete
        with set_context(local_e):
            return header_interface.delete(self.parent.TableType, **payload)

    #VIEW | EXPORT | SESSION
    @IO.Post(router,'/open')
    def open(self, local_e, foreign_e, req_or_ws, **payload): #post
        with set_context(local_e):
            return header_interface.open(self.parent.TableType, **payload)

    @IO.Post(router,'/close')
    def close(self, local_e, foreign_e, req_or_ws, **payload): #post
        with set_context(local_e):
            return header_interface.close(self.parent.TableType, **payload)
            
    #VIEW | EXPORT | SESSION -> FILE | SPACE
    @IO.Post(router,'/cleanup')
    def cleanup(self, local_e, foreign_e, req_or_ws, **payload): #post
        with set_context(local_e):
            return header_interface.cleanup(self.parent.TableType, **payload)

    @IO.Post(router,'/expose')
    def expose(self, local_e, foreign_e, req_or_ws, **payload): #post
        with set_context(local_e):
            return header_interface.expose(self.parent.TableType, **payload)

    @IO.Get(router,'/diff')
    def diff(self, local_e, foreign_e, req_or_ws, **payload): #get
        with set_context(local_e):
            return header_interface.diff(self.parent.TableType, **payload)

    @IO.Get(router,'/diff_future_space')
    def diff_future_space(self, local_e, foreign_e, req_or_ws, struct): #get
        with set_context(local_e):
            return header_interface.diff_future_space(self.parent.TableType, struct)

    
    @IO.Put(router,'/upload')
    def upload_file(self, local_e, foreign_e, req_or_ws, file:UploadFile, metadata:dict={}): #get
        assert self.parent.TableType is File
        with set_context(local_e):
            return header_interface.upload_file( file, metadata)

    @IO.Put(router,'/upload_form')
    def upload_file_with_form(self, local_e, foreign_e, req_or_ws, file : UploadFile, filename:str = None):        
        assert self.parent.TableType is File


        with set_context(local_e):
            if filename:
                return header_interface.upload_file(file, {'name':filename} )
            else:
                return header_interface.upload_file(file )
        
    @IO.Get(router,'/download')
    def download(self, local_e, foreign_e, req_or_ws, id): #get
        assert self.parent.TableType in [File,asc_Space_NamedFile]
        with set_context(local_e):
            res_row = header_interface.find(self.parent.TableType, id)
            if not res_row: return 404

            if isinstance(res_row, File):
                path=file_utils.get().file_on_disc(res_row.id)
                return FileResponse(path=path, filename=path, media_type='binary/blob')
            
            if isinstance(res_row, asc_Space_NamedFile):
                path=file_utils.get().file_on_disc(res_row.cFile.id)
                return FileResponse(path=path, filename=res_row.cName, media_type='binary/blob')

            # res = header_interface.download(self.parent.TableType, id)

        
    # @IO.Put(router,'/upload')
    # def upload(self, local_e, foreign_e, req_or_ws, file:UploadFile, **payload): #get
    #     with set_context(local_e):
    #         return header_interface.upload(self.parent.TableType, **payload)



class USER_interface(Interface_Base):
    TableType = User
    router = APIRouter('/USER')       
    cmds   = _generic_filedb_interface
class SESSION_interface(Interface_Base):
    TableType = Session
    router = APIRouter('/SESSION')    
    cmds   = _generic_filedb_interface
class IMPORT_interface(Interface_Base):
    TableType = Import
    router = APIRouter('/IMPORT')     
    cmds   = _generic_filedb_interface
class EXPORT_interface(Interface_Base):
    TableType = Export
    router = APIRouter('/EXPORT')     
    cmds   = _generic_filedb_interface
class VIEW_interface(Interface_Base):
    TableType = View
    router = APIRouter('/VIEW')       
    cmds   = _generic_filedb_interface
class SPACE_interface(Interface_Base):
    TableType = Space
    router = APIRouter('/SPACE')      
    cmds   = _generic_filedb_interface
class NAMED_SPACE_interface(Interface_Base):
    TableType = asc_Space_NamedSpace
    router = APIRouter('/NAMED_SPACE')
    cmds   = _generic_filedb_interface
class FILE_interface(Interface_Base):
    TableType = File
    router = APIRouter('/FILE')       
    cmds   = _generic_filedb_interface
class NAMED_FILE_interface(Interface_Base):
    TableType = asc_Space_NamedFile
    router = APIRouter('/NAMED_FILE') 
    cmds   = _generic_filedb_interface

class  FileDB_Interface(Interface_Base):
    '''Duel purpose header interface. Utakes Aboserv_Action_State quirries and passes them into functions, as well as the direct interface '''
    router = APIRouter('/FileDB')
    
    USER        = USER_interface
    SESSION     = SESSION_interface
    IMPORT      = IMPORT_interface
    EXPORT      = EXPORT_interface
    VIEW        = VIEW_interface
    SPACE       = SPACE_interface
    NAMED_SPACE = NAMED_SPACE_interface
    FILE        = FILE_interface
    NAMED_FILE  = NAMED_FILE_interface

    def REACT_ws_action(self, websocket, other_e:Foreign_Entity_Base, id:str, topic: Message_Topics.FILE_DB, action:FILEDB_Message_Actions, payload): 
        assert topic is Message_Topics.FILE_DB
        assert isinstance(action, FILEDB_Message_Actions)
        assert isinstance(payload,list)
        table_enum  = FILEDB_Message_Tables(payload[0])
        payload     = payload[1]
        
        interface = getattr(self, table_enum.value)
        interface.REACT_ws_action(self,websocket,other_e,id,topic,action,payload)





