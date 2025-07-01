
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
        
        raise #TODO: Move file

        if do_remove and repl_symlink:
            raise
        elif do_remove:
            fu.remove_file(fp_from)            
        elif repl_symlink:
            temp_path = fu.rename_temp(file_item.path)
            try:
                fu.make_symlink(file_item.path, filepath)
                fu.remove_temp(temp_path)
            except:
                fu.remove_symlink(filepath)
                fu.unname_temp(temp_path, filepath)
                raise


class space_utils:
    ...

fu = file_utils
su = space_utils

class repo_user(repo_interface_base):
    base=User

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
        

    def on_remove(obj):
        ''' Removes file reference '''
        #TODO: Hook into on pre-removal from db
        obj.remove_target(obj)

class repo_NamedFile(repo_interface_base):
    base=asc_Space_NamedFile

    @transaction
    def store(cls, 
              filepath     : str, 
              filename     : str, 
              space        : Space, 
              repl_symlink : bool, 
              do_remove    : bool):
        ''' Store a file to {store} and replace original with symlink where true '''
        _repo_File = cls.db_interface.repo_File

        namedFile_Inst = cls.base()

        file_uid  = fu.get_uid(filepath)
        file_item = _repo_File.store(filepath, file_uid)

        assert file_item.verify_on_disk()

        namedFile_Inst.file  = file_item
        namedFile_Inst.name  = filename
        namedFile_Inst.space = space 

        fu.move_file(filepath,file_item.path,repl_symlink,do_remove) 

        _repo_File.create(file_item)
        cls.create(namedFile_Inst)

    def on_remove(obj):
        ''' Removes file reference '''
        #TODO: Hook into on pre-removal from db
        obj.remove_target(obj)


class repo_File(repo_interface_base):
    base=File

    @transaction
    def store(cls, filepath, uid, repl_symlink=False, do_remove=False ):
        ''' Non-committed file instance '''
        session = cls.context.c_session.get()
        if existing := session.quiery(cls.base).filter(id=uid).first() and existing.verify_on_disk():
            return existing
        elif existing:
            log.log(existing.id, " exists in db, but is not on disk! Uploading")

        file_inst = cls.base()
        file_inst.id = uid
        file_inst.filepath

        fu.move_file(filepath ,
                     uid      ,
                     repl_symlink = repl_symlink,
                     do_remove    = do_remove   ,)

        cls.create(file_inst)

        return file_inst


class repo_Space(repo_interface_base):
    base=Space

    @classmethod
    def store(cls, dp, repl_junction, do_remove):
        _repo_NamedFile = cls.db_interface.repo_NamedFile 
        _repo_NamedSpace = cls.db_interface.repo_NamedSpace 

        space_inst = cls.base()
        
        for file   in db: #TODO
            _NamedFile = _repo_NamedFile.store(file.path,file.name,space_inst,repl_junction,do_remove)
            space_inst.files.append(_NamedFile)
        for folder in db:
            _NamedSpace = _repo_NamedSpace.store(folder.path,folder.name,space_inst,repl_junction,do_remove)
            space_inst.spaces.append(_NamedSpace)
        
        space_inst.id = space_inst.get_id()

        cls.create(space_inst)

        return space_inst

class repo_Export(repo_interface_base):
    base=Export


class repo_Session(repo_interface_base):
    base=Session    