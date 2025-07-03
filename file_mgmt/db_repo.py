
import shutil
import os

from .db_repo_base import repo_interface_base, transaction

from .db_struct import (
    asc_Space_NamedFile,
    asc_Space_NamedSpace,
    File,
    Space,
    Export,
    Session,
    User,
    )

from contextvars import ContextVar

class log:
    ...

class file_utils:
    def get_uid():
        ''' Return UID of file, sha256 hash. Follow symlinks and get sha256 of file'''
    
    def store_file():...

    def rename_temp():...
    def unname_temp():...
    def remove_temp():...
    
    def make_symlink():...

    def remove_symlink():...
    def remove_file():...

    @classmethod
    def move_file(cls, fp_from, fp_to, repl_symlink, do_remove):
        if do_remove and repl_symlink:
            raise
        elif do_remove:
            shutil.move(fp_from,fp_to)
            fu.remove_file(fp_from)
        elif repl_symlink:
            shutil.move(fp_from,fp_to)
            os.symlink(fp_to,fp_from)
        else:
            shutil.copyfile(fp_from,fp_to)

import random
import uuid
class uuid_utils:
    r = random.random(seed = 'STATIC_SEED')
    @classmethod
    def get(cls,keysum: str)->str:
        ...

class space_utils:
    ...

fu = file_utils
su = space_utils

class repo_user(repo_interface_base):
    base=User

    @classmethod
    def make(cls, id, hid):
        inst = cls.base()
        inst.id  = id
        inst.hid = hid
        cls.create(inst)
        return inst

class repo_NamedSpace(repo_interface_base):
    base=asc_Space_NamedSpace

    @classmethod
    def store(cls, 
              dp            : str   ,
              name          : str   ,
              repl_junction : bool  , 
              do_remove     : bool  ,
              ):
        ''' 
        Upload all nested files, folders (through reflective recursion)
        Return Instance of NamedSpace
        '''
        #upload all files via named file instances, 
        _repo_NamedFile  = cls.db_interface.repo_NamedFile  
        _repo_Space = cls.db_interface.repo_Space  
        
        space_inst = _repo_Space.store(dp, repl_junction, do_remove)
        
        nSpace_inst       = cls.base()
        nSpace_inst.name  = name
        nSpace_inst.space = space_inst

        cls.create(nSpace_inst)

        return nSpace_inst
    
    @classmethod
    def from_space(cls,name,space_inst):
        assert isinstance(space_inst,Space)
        nSpace_inst       = cls.base()
        nSpace_inst.name  = name
        nSpace_inst.space = space_inst
        cls.create(nSpace_inst)
        return nSpace_inst

    def on_remove(obj):
        ''' Removes file reference '''
        #TODO: Hook into on pre-removal from db
        obj.remove_target(obj)

class repo_NamedFile(repo_interface_base):
    base=asc_Space_NamedFile

    @classmethod
    def store(cls, 
              filepath     : str, 
              filename     : str, 
              space        : Space, 
              repl_symlink : bool, 
              do_remove    : bool):
        ''' Store a file to {store} and replace original with symlink where true '''
        _repo_File = cls.db_interface.repo_File

        nfile_inst = cls.base()

        file_uid  = fu.get_uid(filepath)
        file_item = _repo_File.store(filepath, file_uid)

        assert file_item.verify_on_disk()

        nfile_inst.file  = file_item
        nfile_inst.name  = filename
        nfile_inst.space = space 

        fu.move_file(filepath,file_item.path,repl_symlink,do_remove) 

        _repo_File.create(file_item)
        cls.create(nfile_inst)

    @classmethod
    def from_file(cls,name,file_inst):
        assert isinstance(file_inst,File)
        nFile_inst       = cls.base()
        nFile_inst.name  = name
        nFile_inst.space = file_inst
        cls.create(nFile_inst)
        return nFile_inst

    def on_remove(obj):
        ''' Removes file reference '''
        #TODO: Hook into on pre-removal from db
        obj.remove_target(obj)
        
class repo_File(repo_interface_base):
    base=File

    @classmethod
    def store(cls, filepath, uid, repl_symlink=False, do_remove=False ):
        ''' Non-committed file instance '''
        session = cls.context.c_session.get()
        if existing := session.quiery(cls.base).filter(id=uid).first() and existing.verify_on_disk():
            return existing
        elif existing:
            log.log(existing.id, " exists in db, but is not on disk! Uploading")

        file = cls.base()
        file.id = uid
        file.filepath

        fu.move_file(filepath ,
                     uid      ,
                     repl_symlink = repl_symlink,
                     do_remove    = do_remove   ,)

        cls.create(file)

        return file

    @classmethod
    def as_named(cls,name,file:File):
        assert isinstance(file,File)
        nFile = asc_Space_NamedFile()
        nFile.cFile = file        
        nFile.cName = name  
        repo_NamedSpace.create(nFile)
        return nFile 
    
class repo_Space(repo_interface_base):
    base=Space

    @classmethod
    def store(cls, dp, repl_junction, do_remove):
        _repo_NamedFile = cls.db_interface.repo_NamedFile 
        _repo_NamedSpace = cls.db_interface.repo_NamedSpace 

        space_inst = cls.base()
        
        for file   in dp: #TODO
            _NamedFile = _repo_NamedFile.store(file.path,file.name,space_inst,repl_junction,do_remove)
            space_inst.files.append(_NamedFile)
        for folder in dp:
            _NamedSpace = _repo_NamedSpace.store(folder.path,folder.name,space_inst,repl_junction,do_remove)
            space_inst.spaces.append(_NamedSpace)
        
        space_inst.id = space_inst.get_id()

        cls.create(space_inst)

        return space_inst
    
    @classmethod
    def as_named(cls,name,space:Space):
        assert isinstance(space,Space)
        nspace = asc_Space_NamedSpace()
        nspace.cSpace = space        
        nspace.cName  = name  
        repo_NamedSpace.create(nspace)
        return nspace 

    @classmethod
    def set_id(cls,space:Space,chain:list=None):
        assert isinstance(space,Space)
        eval_spaces = True
        keysum = ''

        if space.id and chain is None:
            raise Exception('Spaces IDs are not mutable, as contents are not mutable!')
        elif space.id and chain is not None:
            return space.id

        if chain   is None : chain = [space]
        elif space in chain: eval_spaces = False # second level recursion, halt eval of spaces. Should still work as UUID in keysum as struct is in keys
            
        for nF in space.myFiles: 
            assert nF.cFile.id
            keysum += nF.cFile.id + nF.cName

        if eval_spaces:
            for nS in space.mySpaces:
                if not nS.cSpace.id:
                    cls.set_id(nS.cSpace,chain=chain)
                keysum += nS.cSpace.id + nS.cName
        
        space.id = uuid_utils.get(keysum)
        return space.id

class repo_Export(repo_interface_base):
    base=Export

    @classmethod
    def from_file(cls,file,name,dp=None):
        ...

    @classmethod
    def from_namedFile(cls,namedFile,dp=None):
        ...

class repo_Session(repo_interface_base):
    base=Session

    @classmethod
    def make(cls,hid,user:User):        

        session_inst = cls.base()
        session_inst.hid    = hid
        session_inst.myUser = user
        
        cls.create(session_inst)
        
        return session_inst
    

class context():
    File    = ContextVar('File'   , default=None)
    Space   = ContextVar('Space'  , default=None)
    Export  = ContextVar('Export' , default=None)
    Session = ContextVar('Session', default=None)
    User    = ContextVar('User'   , default=None)
    