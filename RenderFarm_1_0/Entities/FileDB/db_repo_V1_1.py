
import hashlib

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

class file_utils:
    def get_uid(filepath):
        ''' Return UID of file, sha256 hash. Follow symlinks and get sha256 of file'''
        #https://docs.python.org/3/library/hashlib.html#hashlib.file_digest
        #May want to thread curl reqs so that other files can be retrieved as required
        fp = os.path.realpath(filepath)
        with open(fp, 'rb', buffering=0) as f:
            return hashlib.file_digest(f,'sha256').hexdigest()
    
    def store_file():...

    def rename_temp():...
    def unname_temp():...
    def remove_temp():...
    
    def make_symlink():...

    def remove_symlink():...
    def remove_file():...

    @classmethod
    def move_file(cls, fp_from, fp_to, repl_symlink, do_remove):
        os.makedirs(os.path.split(fp_to)[0],exist_ok=True)
        if do_remove and repl_symlink:
            raise
        elif do_remove:
            shutil.move(fp_from,fp_to)
            fu.remove_file(fp_from)
        elif repl_symlink:
            shutil.move(fp_from,fp_to)
            os.symlink(fp_to,fp_from)
        else:
            shutil.copyfile(fp_from,fp_to, follow_symlinks=True)

class repo_user():
    base=User

class repo_NamedSpace():
    base=asc_Space_NamedSpace

class repo_NamedFile():
    base=asc_Space_NamedFile

class repo_File():
    base=File

class repo_Space():
    base=Space

class repo_Export():
    base=Export

class repo_Session():
    base=Session
