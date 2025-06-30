
from .db_struct_base import repo_interface_base

from .db_struct import (
    asc_Space_NamedFile,
    asc_Space_NamedSpace,
    File,
    Space,
    Export,
    Session,
    User,
    )

class user_repo(repo_interface_base):
    base=User

class asc_Space_NamedFile(repo_interface_base):
    base=asc_Space_NamedFile

class asc_Space_NamedSpace(repo_interface_base):
    base=asc_Space_NamedSpace

class File(repo_interface_base):
    base=File

class Space(repo_interface_base):
    base=Space

class Export(repo_interface_base):
    base=Export

class Session(repo_interface_base):
    base=Session