
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
    def get_uid():...
    
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

class repo_File(repo_interface_base):
    base=File
    # @transaction
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

        fu.move_file(filepath,
                     uid,
                     repl_symlink=repl_symlink,
                     do_remove=do_remove)

        return file_inst


class repo_Space(repo_interface_base):
    base=Space

class repo_Export(repo_interface_base):
    base=Export

class repo_Session(repo_interface_base):
    base=Session    