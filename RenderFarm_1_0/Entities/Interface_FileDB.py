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

from functools  import partial, wraps
from typing     import TypeAlias

from starlette.datastructures import UploadFile as star_Upload_File


import asyncio

AnyTableType : TypeAlias = User|Session|Import|Export|View|asc_Space_NamedSpace|asc_Space_NamedFile|Space|File


from contextlib  import contextmanager
from contextvars import ContextVar

from .DB_Interface_Common import _transaction, session_cm

FileDB_c_Engine    = ContextVar('FileDB_c_Engine'  ,default = None) 
FileDB_c_session   = ContextVar('FileDB_c_session'  ,default = None) 
FileDB_c_savepoint = ContextVar('FileDB_c_savepoint',default = None) 
file_utils         = ContextVar('FileDB_c_file_utils', default= None)
    
FileDB_transaction = partial(_transaction._wrapper, FileDB_c_Engine, FileDB_c_session, FileDB_c_savepoint)
FileDB_Session_CM  = partial(session_cm, FileDB_c_Engine ,FileDB_c_session ,FileDB_c_savepoint)

class _header_interface():
    def _update(self,table,row_item,data:dict):
        for k,v in data.items():
            if k in table._ext_allowable_:
                setattr(row_item,k)
            else:
                raise KeyError(f'K:V {k}:{v} IS NOT ALLOWED TO BE SET ON {table}')

    @FileDB_transaction()
    def find[T:AnyTableType](self,session, table:T, item_id:str)->T:  #Get
        return session.query(table).filter(table.id == item_id).first()

    @FileDB_transaction()
    def query(self,session, table, **defintions):  #Get
        return session.query(table).all(**defintions)

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
    

    @FileDB_transaction()
    def create(self,session, table, **payload): #Post 
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
        session.add(val)
        return val
    
    @FileDB_transaction()
    def update(self,session, table, target_row, **payload): #Patch
        self._update(target_row,payload)
    
    @FileDB_transaction()
    def delete(self,session, table, target_row, **payload): #Delete
        session.remove(target_row)

    def diff(self, table, mode:str, object_def:dict)->bool:
        ''' Treat {key : (_Any,(value_series,...))} as an operation to parse '''
        ...

    def data(self, table, target_row):
        ...



    #SESSION
    @FileDB_transaction(filter = lambda x: x is Session)
    def open(self, table, target_row):
        target_row.isOpen = True

    @FileDB_transaction(filter = lambda x: x is Session)
    def close(self, table, target_row):
        target_row.isFalse = True


    #VIEW | IMPORT | EXPORT | NAMEDSPACE | NAMEDFILE -> SPACE | FILE

    @FileDB_transaction(filter = lambda x: x in [Import,Export,View,asc_Space_NamedSpace,asc_Space_NamedFile,Space,File])
    def expose(self, table, target_row, **payload): 
        raise NotImplementedError('TODO: PORT FROM ORIGINAL')

    def cleanup(self, table, target_row, **payload): 
        raise NotImplementedError('Settup Intial routine first!')


    #VIEW | IMPORT | EXPORT | NAMEDSPACE | NAMEDFILE -> SPACE
    # @FileDB_transaction(filter = lambda x: x in [Import,Export,View,asc_Space_NamedSpace,asc_Space_NamedFile,Space,File])

    def diff_future(self, files:list[str], spaces:list[str])->list: #get
        ''' Determine elements that need to be uploaded by hash diff'''

        need_hashes  = []
        for key in files:
            if self.find(File , key) is None:
                need_hashes.append( key)
        for key in spaces:
            if self.find(Space, key) is None:
                need_hashes.append( key)
        return need_hashes

    # @FileDB_transaction()
    def create_named_file_from_structure(self,session, structure:dict, pspace_id):  #requered for search.
        ''' Non-Transactional as it requires a parent '''
        if (nfile:=self.find(File, structure['full_hash'])) is not None: return nfile
        nfile = asc_Space_NamedFile()

        if (file:=self.find(File,structure['data_hash'])) is None:
            raise Exception('FILE DOES NOT EXIST ON DB! Delayed upload not yet supported!!:',structure['data_hash'], 'of', structure)
            
        nfile.cFile = file
        return nfile

    @FileDB_transaction()
    def create_named_space_from_structure(self,session, structure:dict, pspace_id)->asc_Space_NamedSpace:
        ''' Non-Transactional as it requires a parent '''
        if (nspace:=self.find(asc_Space_NamedSpace, structure['full_hash'])) is not None: return nspace
        nspace = asc_Space_NamedSpace()

        if (space:=self.find(Space, structure['data_hash'])) is None:
            space = self.create_space_from_structure(structure)
        nspace.cSpace = space
        session.add(nspace)
        return nspace

    @FileDB_transaction()
    def create_space_from_structure(self,session, structure):
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
        session.add(space)
        return space
    
    @FileDB_transaction()
    async def upload_file(self,session, file:UploadFile|bytearray, metadata:dict={})->File:
        if data_hash:=metadata.get('data_hash'):
            if filerow:=self.find(File,data_hash):
                if fp:=file_utils.get().file_on_server(filerow):
                    print(f'WARNING! FILE WITH DATA_HASH {data_hash} ALREADY UPLOADED AND ON DISC AT {fp}, DUMPING AND RETURING ON_DISC')
                    if isinstance(file, UploadFile): await file.close()
                    return filerow
        
        if isinstance(file, star_Upload_File): 
            data_hash = uuid_utils.get_bytearray_hash(file.file)
        else:                            
            data_hash = uuid_utils.get_bytearray_hash(file)
        
        if _mdata_hash:= metadata.get('data_hash',None):
            if data_hash != _mdata_hash:
                print(f'MANAGER DID NOT GET THE SAME BYTE HASH:',data_hash,  metadata['data_hash'], metadata)


        if (filerow:=self.find(File,data_hash)) is None: filerow = File()
        elif fp:=file_utils.get().file_on_server(filerow): 
            if isinstance(file, UploadFile): await file.close()
            print(f'WARNING! FILE WITH DATA_HASH {data_hash} ALREADY UPLOADED AND ON DISC AT {fp}, DUMPING AND RETURING ON_DISC')
            return filerow
        
        if isinstance(file, star_Upload_File):
            await file.seek(0)
            # raise Exception(file.file.read())
            # data.seek(0)
        
            await file_utils.get().dump_UploadFile(file.file,data_hash=data_hash)
            await file.close()
        else:
            await file_utils.get().dump_bytearray(file,data_hash=data_hash)

        filerow.id = data_hash
        session.add(filerow)
        return filerow
    
    # def upload_import_export(self, table, space_id, session_id, user_id, **container_data,):
    #     container = self._create_import_export(table, session_id, user_id, container_data)
    #     container.mySpaceId = space_id
    #     Active_Session.get().append(container)

    # def upload_view(self, table, space_id, session_id, **container_data):
    #     container = self._create_import_export(table, session_id, container_data)
    #     container.mySpaceId = space_id
    #     Active_Session.get().append(container)
        
    
    @FileDB_transaction(filter = lambda x: x in [Import,Export,View,asc_Space_NamedSpace,asc_Space_NamedFile,Space,File])
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



class  FileDB_Interface(Interface_Base):
    '''Duel purpose header interface. intakes Aboserved_Action_State quirries and passes them into functions, as well as the direct interface '''
    Route_Subpath = '/FileDB'
    router = APIRouter()

    def REACT_ws_action(self, websocket, other_e:Foreign_Entity_Base, id:str, topic: Message_Topics.FILE_DB, action:FILEDB_Message_Actions, payload): 
        assert topic is Message_Topics.FILE_DB
        assert isinstance(action, FILEDB_Message_Actions)
        assert isinstance(payload,list)
        table_enum  = FILEDB_Message_Tables(payload[0])
        payload     = payload[1]
        
        interface = getattr(self, table_enum.value)
        interface.REACT_ws_action(self,websocket,other_e,id,topic,action,payload)


    get_table = {
        '/USER': User,
        '/SESSION': Session,
        '/IMPORT': Import,
        '/EXPORT': Export,
        '/VIEW': View,
        '/SPACE': Space,
        '/NAMED_SPACE': asc_Space_NamedSpace,
        '/FILE': File,
        '/NAMED_FILE': asc_Space_NamedFile
    }

    #ALL:
    # @IO.Get(router,'/{TABLENAME}/raw_table')
    # def raw_data(self, local_e, foreign_e, req_or_ws, TABLENAME, uid):  #Get
        # table=self.get_table[TABLENAME]
#         self.parent.TableType._template_id #DEFER: Links to other tables by type? Websocket stream tables?
    #     

    # @IO.Get(router,'/{TABLENAME}/raw_data/{uid}')
    # def raw_data(self, local_e, foreign_e, req_or_ws, TABLENAME, uid):  #Get
        # table=self.get_table[TABLENAME]
#         return  header_interface.find(table, uid)._as_link_dict() #DEFER: Links to other tables by type?
    #     


    @IO.Get(router,'/{TABLENAME}/query')
    def query(self, local_e, foreign_e, req_or_ws, TABLENAME, **payload):  #Get
        table=self.get_table[TABLENAME]
        return [x.uid for x in header_interface.query(table,**payload)]
        
    
    @IO.Get(router,'/{TABLENAME}/find')
    def find(self, local_e, foreign_e, req_or_ws, TABLENAME, **payload):  #Get
        table=self.get_table[TABLENAME]
        return header_interface.find(table, **payload).uid
        

    @IO.Get(router,'/{TABLENAME}/table')
    def data(self, local_e, foreign_e, req_or_ws, TABLENAME, **payload):  #Get
        table=self.get_table[TABLENAME]
        return header_interface.data(table, **payload)
        

    @IO.Post(router,'/{TABLENAME}/table')
    def create(self, local_e, foreign_e, req_or_ws, TABLENAME, **payload): #Post
        table=self.get_table[TABLENAME]
        return header_interface.create(table, **payload)
        

    @IO.Patch(router,'/{TABLENAME}/table')
    def update(self, local_e, foreign_e, req_or_ws, TABLENAME, **payload): #Patch
        table=self.get_table[TABLENAME]
        return header_interface.update(table, **payload)
        

    @IO.Delete(router,'/{TABLENAME}/table')
    def delete(self, local_e, foreign_e, req_or_ws, TABLENAME, **payload): #Delete
        table=self.get_table[TABLENAME]
        return header_interface.delete(table, **payload)
        

    #VIEW | EXPORT | SESSION
    @IO.Post(router,'/{TABLENAME}/open')
    def open(self, local_e, foreign_e, req_or_ws, TABLENAME, **payload): #post
        table=self.get_table[TABLENAME]
        return header_interface.open(table, **payload)
        

    @IO.Post(router,'/{TABLENAME}/close')
    def close(self, local_e, foreign_e, req_or_ws, TABLENAME, **payload): #post
        table=self.get_table[TABLENAME]
        return header_interface.close(table, **payload)
        
            
    #VIEW | EXPORT | SESSION -> FILE | SPACE
    @IO.Post(router,'/{TABLENAME}/cleanup')
    def cleanup(self, local_e, foreign_e, req_or_ws, TABLENAME, **payload): #post
        table=self.get_table[TABLENAME]
        return header_interface.cleanup(table, **payload)
        

    @IO.Post(router,'/{TABLENAME}/expose')
    def expose(self, local_e, foreign_e, req_or_ws, TABLENAME, **payload): #post
        table=self.get_table[TABLENAME]
        return header_interface.expose(table, **payload)
        

    @IO.Get(router,'/{TABLENAME}/diff')
    def diff(self, local_e, foreign_e, req_or_ws, TABLENAME, **payload): #get
        table=self.get_table[TABLENAME]
        return header_interface.diff(table, **payload)
        
    
    @IO.Put(router,'/{TABLENAME}/upload')
    async def upload_data_indv(self, local_e, foreign_e, req_or_ws, TABLENAME, file:UploadFile, metadata:dict={}): #get
        table=self.get_table[TABLENAME]
        assert self.parent.TableType is File
        return await header_interface.upload_file(file, metadata)
        
        
    @IO.Post(router,'/FILE/upload_file')
    async def upload_file(self, local_e, foreign_e, req_or_ws, file : UploadFile):        
        return (await header_interface.upload_file(file)).id

        

    @IO.Get(router,'/FILE/upload_file_form')
    def upload_file_form(self, local_e, foreign_e, req_or_ws):        
        return local_e.fapi_db_templates.TemplateResponse(
            "/upload/upload.html",
            {   'request' : req_or_ws, 
                'Manager_Name':local_e.settings.label},
        )
        
    @IO.Get(router,'/{TABLENAME}/download')
    def download(self, local_e, foreign_e, req_or_ws, TABLENAME, id): #get
        table=self.get_table[TABLENAME]
        assert table in [File,asc_Space_NamedFile]
        res_row = header_interface.find(table, id)
        
        if not res_row: return 404

        if isinstance(res_row, File):
            path=file_utils.get().file_on_disc(res_row.id)
            return FileResponse(path=path, filename=path, media_type='binary/blob')
        
        if isinstance(res_row, asc_Space_NamedFile):
            path=file_utils.get().file_on_disc(res_row.cFile.id)
            return FileResponse(path=path, filename=res_row.cName, media_type='binary/blob')

            # res = header_interface.download(table, id)

        
    # @IO.Put(router,'/{TABLENAME}/upload')
    # def upload(self, local_e, foreign_e, req_or_ws, TABLENAME, file:UploadFile, **payload): #get
    # table=self.get_table[TABLENAME]
#         return header_interface.upload(table, **payload)
    #     




