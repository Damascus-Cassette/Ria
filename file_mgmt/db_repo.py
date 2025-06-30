
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

class utils():
    def file_uid(filepath):
        ...
    def file_to_symlink(filepath,uid):
        ...
u = utils



class repo_user(repo_interface_base):
    base=User

class repo_NamedFile(repo_interface_base):
    base=asc_Space_NamedFile

class repo_NamedSpace(repo_interface_base):
    base=asc_Space_NamedSpace

class repo_File(repo_interface_base):
    base=File



    @classmethod
    def ensure_in_db(cls, filepath, replace=True)->str:
        session = cls.db_interface.c_session.get()
        uid     = cls.get_uid(filepath)
        
        if not cls.uid_in_db(uid):
            store_fp = cls.find_place(uid)
            cls.move_item()

        if replace:
            ...

        return uid

    @classmethod
    def move_item(cls,fp_from,fp_to):
        ...

    @classmethod
    def find_place(cls,filepath,uid)->str:
        return

    @classmethod
    def get_uid(cls,filepath)->str:
        return
        
    @classmethod
    def uid_in_db(cls,uid)->bool:
        session = cls.db_interface.c_session.get()
        return any(session.query(cls.base).filter(id = uid).all())

class repo_Space(repo_interface_base):
    base=Space

class repo_Export(repo_interface_base):
    base=Export

class repo_Session(repo_interface_base):
    base=Session    