
from .db_repo_base import repo_interface_base

from .db_struct import (
    asc_Space_NamedFile,
    asc_Space_NamedSpace,
    File,
    Space,
    Export,
    Session,
    User,
    )

class repo_user(repo_interface_base):
    base=User

class repo_NamedFile(repo_interface_base):
    base=asc_Space_NamedFile

class repo_NamedSpace(repo_interface_base):
    base=asc_Space_NamedSpace

class repo_File(repo_interface_base):
    base=File

class repo_Space(repo_interface_base):
    base=Space

class repo_Export(repo_interface_base):
    base=Export

class repo_Session(repo_interface_base):
    base=Session