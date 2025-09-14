from pathlib         import Path
from contextvars     import ContextVar
from contextlib      import contextmanager
from multiprocessing import Process
from typing          import Self

import hashlib
import os
import random
import uuid
import shutil
import asyncio


class file_utils():
    ''' Contextual File movment, in relation to settings defined structures '''

    def __init__(self, settings):
        ...

    async def dump_bytearray(self, data:bytearray, data_hash:str=None):
        if not data_hash:
            data_hash = uuid_utils.get_bytearray_hash(data)
        with open(self.file_loc(data_hash),'wb') as f:
            f.write(data)

    def move_file(self, fp_from, fp_to, repl_symlink, do_remove):
        os.makedirs(os.path.split(fp_to)[0],exist_ok=True)
        if do_remove and repl_symlink:
            raise
        elif do_remove:
            shutil.move(fp_from,fp_to)
            self.remove_file(fp_from)
        elif repl_symlink:
            shutil.move(fp_from,fp_to)
            os.symlink(fp_to,fp_from)
        else:
            shutil.copyfile(fp_from,fp_to, follow_symlinks=True)

class uuid_utils:

    @classmethod
    def get_file_hash(cls,filepath):
        ''' Return UID of file, sha256 hash. Follow symlinks and get sha256 of file'''
        #https://docs.python.org/3/library/hashlib.html#hashlib.file_digest
        #May want to thread curl reqs so that other files can be retrieved as required
        fp = os.path.realpath(filepath)
        with open(fp, 'rb', buffering=0) as f:
            cls.get_bytearray_hash(f)

    def get_bytearray_hash(obj:bytearray):
        ''' Abstraction to allow for spooled-file use'''
        return hashlib.file_digest(obj,'sha256').hexdigest()

    @classmethod
    def get_str_uuid(cls,keysum: str)->str:
        r = random.Random()
        r.seed(keysum)
        return str(uuid.UUID(bytes = bytes(r.getrandbits(8) for _ in range(16))))

    @classmethod
    def get_dict_uuid(cls, data:dict)->str:
        r = random.Random()
        r.seed(str(cls.sorted_recur_dict(data)))
        return str(uuid.UUID(bytes = bytes(r.getrandbits(8) for _ in range(16))))

    @staticmethod
    def get_file_metadata(vis_path)->dict:
        stats = Path(vis_path).stat(follow_symlinks=True)
        return {'name':Path(vis_path).name, 'st_size': stats.st_size}

    @staticmethod
    def get_folder_metadata(vis_path)->dict:
        return {'name':Path(vis_path).name}

    @classmethod
    def sorted_recur_dict(cls,data:dict):
        print ('WARNING: DICT SORT IS NOT IMPLAMENTED YET AND MAY CAUSE NON-DETERM') 
        return data
    
    @staticmethod
    def create_structure(path):
        with folder_walk_session():
            if Path(path).is_dir():
                return Folder_Object(path)
            else:
                return File_Object(path)

folders_in_session : dict[str, 'File_Object']   = ContextVar('folders_in_session', default = None) 
files_in_session   : dict[str, 'Folder_Object'] = ContextVar('files_in_session',   default = None)
files_in_server    : list[str] = ContextVar('files_in_session',   default = None)


@contextmanager
def folder_walk_session():
    t1 = files_in_session.set({})
    t2 = folders_in_session.set({})
    yield
    files_in_session.reset(t1)
    folders_in_session.reset(t2)

class Folder_Object():
    children_folders : list
    children_files   : list

    data_hash_src : None|Self = None

    folder_path   : str
    real_path     : str #Refering to post -symlink follow path

    def __init__(self,folder_path):
        self.children_folders = []
        self.children_files   = []
        
        real_path = str(Path(folder_path).resolve())

        self.folder_path = folder_path
        self.real_path   = real_path

        if existing := folders_in_session.get().get(real_path,None):
            self.data_hash_src = existing
        else: 
            files_in_session.get()[real_path] = self
            self.discovery_children(real_path)

    def discover_children(self,real_path):
        for path in Path(real_path).iterdir():
            p_path = Path(path)
            if p_path.isdir():
                self.children_folders.append(Folder_Object(path))
            else:
                self.children_files.append(File_Object(path))

    def full_hash(self):
        data_hash     = self.data_hash
        metadata_hash = self.metadata_hash
        return uuid_utils.get_str_uuid(data_hash+metadata_hash)

    @property
    def data_hash(self):
        ''' uuid-hash of content's full hashes '''
        if self.data_hash_src: 
            return self.data_hash_src.data_hash
        
        lst = []
        for x in self.child_folders:
            lst.append(x.full_hash)
        for x in self.child_files:
            lst.append(x.full_hash)
        return uuid_utils.get_str_uuid(''.join(lst))

    @property
    def metadata_hash(self):
        ''' Metadata of self.folder_path.name (view of folder) '''
        return uuid_utils.get_dict_uuid(uuid_utils.get_folder_metadata(self.folder_path))

    def _export_struct_(self):
            if self.data_hash in files_in_server.get().keys():
                return {'_type':'NAMEDFOLDER', 'full_hash': self.full_hash, 'metadata' : self.metadata, 'datahash' : self.data_hash, 'children' : self._export_children_()}
            else:
                return {'_type':'NAMEDFOLDER', 'full_hash': self.full_hash, 'metadata' : self.metadata, 'datahash' : self.data_hash, 'children' : self.data_hash}

    def _export_children_(self):
        lst = []
        for x in self.child_folders:
            lst.append(x._export_struct_())
        for x in self.child_files:
            lst.append(x._export_struct_())
        return lst
        
def find_filepath_hashes_in_multiprocess(filepath, metadata_path=None):
    with open(filepath,'r') as f:
        file_hash = uuid_utils.get_bytearray_hash(f)
    
    if metadata_path: metadata = uuid_utils.get_folder_metadata(metadata_path)
    else:             metadata = uuid_utils.get_folder_metadata(filepath)

    metadata_hash = uuid_utils.get_dict_uuid(metadata)
    return file_hash, metadata_hash

class File_Object():

    _hash_calculated : bool = False

    @staticmethod
    def run_all_in_session():
        coroutines = []
        for x in files_in_session.get():
            coroutines.append(x.get_hashes())
        asyncio.gather(coroutines)
        return

    def __init__(self,file_path):

        real_path = str(Path(file_path).resolve())

        self.file_path = file_path
        self.real_path = real_path

        if existing := folders_in_session.get().get(real_path,None):
            self.data_hash_src = existing
        else: 
            files_in_session.get()[real_path] = self
            self.discovery_children(real_path)

    async def get_hashes(self):
        if isinstance(self.file_hash, File_Object):
            p = Process(find_filepath_hashes_in_multiprocess, args = (self.real_path, ) )
            p = Process.start()
            self.file_hash, self.metadata_hash = p.join()
        else:
            self.metadata = uuid_utils.get_file_metadata(self.filepath)
            self.metadata_hash = uuid_utils.get_dict_uuid(self.metadata)
        self._hash_calculated = True

    @property
    def get_file_hash(self,):
        assert self._hash_calculated
        if isinstance(self.file_hash, File_Object):
            return self.file_hash.get_file_hash
        return self.file_hash

    def full_hash(self):
        file_hash     = self.get_file_hash
        metadata_hash = self.metadata_hash
        return uuid_utils.get_str_uuid(file_hash+metadata_hash)
    
    def _export_struct_(self):
        return {'_type':'NAMEDFILE', 'full_hash': self.full_hash, 'metadata' : self.metadata, 'datahash' : self.file_hash}
        
#target structure to upload: each file, nested dict of {name:(type, metadata, key, children:[])} that culls if obj already exists on server