
from contextvars import ContextVar
from pathlib import Path
from typing import Self

root = ContextVar('root', default=None)
c_ignore_hashes = ContextVar('ignore_hashes', default=None)

import hashlib
import os
import random
import uuid
import asyncio


class _def_dict_list():
    def __missing__(self,key):
        self[key] = inst = []
        return inst

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
        if Path(path).is_dir():
            prim = Folder_Object(path)
        else:
            prim = File_Object(path)
        return prim


class Folder_Object():
    child_folders : list['Folder_Object']
    child_files   : list['File_Object'  ]

    _data_hash : Self|None = None

    real_path_dedup : None|dict[str,'Folder_Object']

    def __init__(self, path):
        reset = False
        if root.get() is None:
            self.real_path_dedup = {}
            t = root.set(self)
            reset = True


        self.real_path = Path(path).resolve()
        self.path      = path

        
        if (first:=root.get().real_path_dedup.get(self.real_path, None)) is not None:
            self._data_hash = first
        else:
            root.get().real_path_dedup[self.real_path] = self
            self.child_folders = []
            self.child_files   = []
            self.discover_children()

        if reset: root.reset(t)


    def discover_children(self):
        for path in Path(self.real_path).iterdir():
            if Path(path).is_dir():
                self.child_folders.append(Folder_Object(path))        
            else:
                self.child_files.append(File_Object(path))  
    
    @property
    def data_hash(self):
        if isinstance(self._data_hash, Folder_Object):
            return self._data_hash.data_hash
        else:
            return uuid_utils.get_str_uuid(''.join((x.full_hash for x in (*self.child_files, *self.child_folders))))

    @property
    def meta_hash(self):
        return uuid_utils.get_dict_uuid(uuid_utils.get_folder_metadata(self.path))

    @property 
    def full_hash(self):
        return uuid_utils.get_str_uuid(self.data_hash + self.meta_hash)
                
    def _export_struct_(self, ignore_hashes=tuple()):
        reset = False
        if root.get() is None: 
            t=root.set(self)
            t1 = c_ignore_hashes.set(ignore_hashes)
            reset = True

        if self.data_hash in c_ignore_hashes.get():
            val =  {'_type':'NAMEDFOLDER', 'metadata' : uuid_utils.get_folder_metadata(self.path) ,'full_hash': self.full_hash, 'meta_hash' : self.meta_hash, 'data_hash' : self.data_hash, 'children' : self.data_hash}
        else:
            val =  {'_type':'NAMEDFOLDER', 'metadata' : uuid_utils.get_folder_metadata(self.path) ,'full_hash': self.full_hash, 'meta_hash' : self.meta_hash, 'data_hash' : self.data_hash, 'children' : self._export_children_()}

        if reset: 
            root.reset(t) 
            c_ignore_hashes.reset(t1)
        return val

    def _export_children_(self):
        lst = []
        for x in self.child_folders:
            lst.append(x._export_struct_())
        for x in self.child_files:
            lst.append(x._export_struct_())
        return lst
    

    def calculate_file_hashes(self):
        for x in self.iter_all_unique_files():
            x.calculate_file_hashes()
        # self.dedup_files_post_hash()
        # self.dedup_folders_post_hash()

    def get_unique_file_datahash_list(self)->list:
        return list(set(x.data_hash for x in self.iter_all_unique_files()))
        
    # def dedup_files_post_hash(self):
    #     ''' Ensure that _data_hash is convergent in all items'''
    #TODO: Will have to be recursive
    #     di = _def_dict_list()
    #     for x in self.iter_all_unique_files():
    #         di[x.data_hash()]

    def iter_all_unique_files(self):
        assert hasattr(self, 'real_path_dedup') #is root object
        for x in self.real_path_dedup.values():
            if isinstance(x,File_Object):
                yield x

    def iter_all_unique_folders(self):
        assert hasattr(self, 'real_path_dedup') #is root object
        for x in self.real_path_dedup.values():
            if isinstance(x,Folder_Object):
                yield x
            


class File_Object():

    def __init__(self, path):
        reset = False
        if root.get() is None:
            self.real_path_dedup = {}
            t = root.set(self)

            reset = True

        self.real_path = Path(path).resolve()
        self.path      = path
        
        if (first:=root.get().real_path_dedup.get(self.real_path, None)) is not None:
            self._data_hash = first
        else:
            root.get().real_path_dedup[self.real_path] = self

        if reset:
            root.reset(t) 

    
    real_path_dedup : None|dict[str,'Folder_Object']
    _data_hash      : None|Self = None

    
    def calculate_file_hashes(self,):
        #TODO: Optimize between processes as required!
        with open(self.real_path,'rb') as f:
            self._data_hash =  uuid_utils.get_bytearray_hash(f)
            self._hash_calcuated = True
    
    def get_file_datahash_list(self)->list:
        return [self.data_hash]
        


    @property
    def data_hash(self):
        if isinstance(self._data_hash, File_Object):
            return self._data_hash.data_hash
        else:
            assert self._hash_calcuated
            return self._data_hash
    
    @property
    def meta_hash(self):
        return uuid_utils.get_dict_uuid({'name':Path(self.path).name})

    @property 
    def full_hash(self):
        return uuid_utils.get_str_uuid(self.data_hash + self.meta_hash)

    def _export_struct_(self, ignore_hashes=tuple()):
        return {'_type':'NAMEDFILE', 'metadata' : uuid_utils.get_file_metadata(self.path), 'full_hash': self.full_hash, 'meta_hash' : self.meta_hash, 'data_hash' : self.data_hash}

    