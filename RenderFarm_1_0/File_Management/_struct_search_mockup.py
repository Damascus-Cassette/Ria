

from contextvars import ContextVar
from contextlib  import contextmanager
from multiprocessing import Process
from typing import Self

folders_in_session : dict[str, 'file_object']   = ContextVar('folders_in_session', default = None) 
files_in_session   : dict[str, 'folder_object'] = ContextVar('files_in_session',   default = None)


import asyncio

@contextmanager
def session():
    t1 = files_in_session.set({})
    t2 = folders_in_session.set({})
    yield
    files_in_session.reset(t1)
    folders_in_session.reset(t2)



def get_metadata_as_dict():
    #Get the original file's metadata. Not the symlinks
    ...

def find_bytearray_hashe(bytearray):
    return statics.uuid.hexdigest(bytearray)

def find_dict_hash(data:dict):
    return statics.from_data(data)

def find_filepath_hashes_multiprocess(filepath, metadata=None):
    with open(filepath,'r') as f:
        file_hash = find_bytearray_hashe(f)
    if metadata is None:
        metadata=get_metadata_as_dict(filepath)
    metadata_hash = find_dict_hash(metadata)


class folder_object():    
    # folder_hash   : str #Hashsum of contents
    # metadata_hash : str #Source junction|folder's name. Additional Metadata is not kept anywhere

    def __init__(self,folder_path):
        self.children_files   = []
        self.children_folders = []

        real_path = ensure_original_path(folder_path)

        self.folder_path = folder_path
        self.real_path   = real_path    

        if existing := files_in_session.get().get(real_path,None):
            self.folder_hash = existing
        else: 
            files_in_session.get()[real_path] = self
            self.discovery_children(real_path)
    
    def discovery_children(self,real_path):
        for folder in os.dir(real_path).dirs:
            self.children_folders.append(folder_object(folder))
        for file in os.dir(real_path).files:
            self.children_files.append(folder_object(folder))
        
    def full_hash(self):
        data_hash     = self.folder_hash
        metadata_hash = self.metadata_hash
        return statics.from_data(data_hash+metadata_hash)
    
    @property
    def folder_hash(self):
        lst = []
        for x in self.child_folders:
            lst.append(x.full_hash)
        for x in self.child_files:
            lst.append(x.full_hash)
        return statics.uuid.from_data(lst)

    @property
    def metadata_hash(self):
        ''' Metadata of self.folder_path.name (view of folder) '''
        return self.folder_path.name


class file_object():
    ''' File rep, with (Self-side) referencing hash deferal based on duplicate paths in the same session '''

    filepath      : str
    file_hash     : str | Self  #IE if two symlinks are the same file under the hood.
    metadata_hash : str
    _hash_calculated : bool = False

    def __init__(self, filepath):
        real_path = ensure_original_path(filepath)
        if real := files_in_session.get().get(real_path,None):
            self.file_hash = real
        else:
            files_in_session.get()[real_path] = self
        self.filepath = filepath
        self.real_path = real_path

    @staticmehod
    def run_all_in_session(self,):
        coroutines = []
        for x in files_in_session.get():
            coroutines.append(x.get_hashes())
        asyncio.gather(coroutines) 

    async def get_hashes(self):
        if isinstance(self.file_hash, file_object) 
            p = Process(find_filepath_hashes_multiprocess, args = (self.real_path, ) )
            p = Process.start()
            self.file_hash, self.metadata_hash = p.join()
        else:
            self.metadata = get_metadata_as_dict(self.filepath)
            self.metadata_hash = find_dict_hash(self.filepath.filename, self.metadata)
        self._hash_calculated = True

    @property
    def get_file_hash(self,):
        if isinstance(self.file_hash, file_object):
            return self.file_hash.get_file_hash
        return self.file_hash

    def full_hash(self):
        file_hash = self.get_file_hash
        metadata_hash = self.metadata_hash
        return statics.from_data(file_hash+metadata_hash)
        
        