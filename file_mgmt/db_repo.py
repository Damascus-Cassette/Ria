
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

class classproperty():
    #https://stackoverflow.com/questions/5189699/how-to-make-a-class-property
    def __init__(self,func):
        self.func = func
    def __get__(self,cls,container):
        return self.func(container)

import hashlib
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

import random
import uuid
class uuid_utils:
    
    @classmethod
    def get(cls,keysum: str)->str:
        r = random.Random()
        r.seed(keysum)
        return str(uuid.UUID(bytes = bytes(r.getrandbits(8) for _ in range(16))))


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
        # cls.create(inst)
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
        _repo_Space = cls.db_interface.repo_Space  
        
        space_inst = _repo_Space.store(dp, repl_junction, do_remove)
        
        nSpace_inst        = cls.base()
        nSpace_inst.hid    = name
        nSpace_inst.pSpace = space_inst

        # cls.create(nSpace_inst)

        return nSpace_inst
    
    @classmethod
    def from_space(cls,name,space_inst):
        assert isinstance(space_inst,Space)
        nSpace_inst       = cls.base()
        nSpace_inst.name  = name
        nSpace_inst.space = space_inst
        # cls.create(nSpace_inst)
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
            #   do_create    : bool = False):
        ''' Store a file to {store} and replace original with symlink where true '''
        _repo_File = cls.db_interface.repo_File


        file = _repo_File.store(filepath)
        assert _repo_File.verify_on_disk(file)
        fu.move_file(filepath,_repo_File.path(file),repl_symlink,do_remove) 
        # _repo_File.create(file)


        nFile = cls.base()
        nFile.cName  = filename
        nFile.cFile  = file
        nFile.pSpace = space

        # if do_create:
        #     cls.create(nFile)
        
        return nFile

    @classmethod
    def from_file(cls,name,file_inst):
        assert isinstance(file_inst,File)
        nFile_inst       = cls.base()
        nFile_inst.name  = name
        nFile_inst.space = file_inst
        # cls.create(nFile_inst)
        return nFile_inst

    def on_remove(obj):
        ''' Removes file reference '''
        #TODO: Hook into on pre-removal from db
        obj.remove_target(obj)
        
class repo_File(repo_interface_base):
    base=File

    @transaction
    def store(cls, filepath, repl_symlink=False, do_remove=False ):
        session = cls.db_interface.c_session.get()
        uid = fu.get_uid(filepath)

        if existing := session.query(cls.base).filter_by(id=uid).first() and existing.verify_on_disk():
            return existing
        elif existing:
            log.log(existing.id, " exists in db, but is not on disk! Uploading")

        file = cls.base()
        
        file.id = uid

        fu.move_file(filepath ,
                     cls.path(file),
                     repl_symlink = repl_symlink,
                     do_remove    = do_remove   ,
                     )

        return file

    @classmethod
    def as_named(cls,name,file:File):
        assert isinstance(file,File)
        nFile = asc_Space_NamedFile()
        nFile.cFile = file        
        nFile.cName = name  
        # repo_NamedSpace.create(nFile)
        return nFile 
    
    @classmethod
    def verify_on_disk(cls,file):
        return os.path.exists(cls.path(file))

    @classmethod
    def path(cls,file):
        with cls.db_interface.repo_cm(File=file):
            return cls.db_interface.settings.database.filepaths.store

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

        # cls.create(space_inst)

        return space_inst
    
    @classmethod
    def as_named(cls,name,space:Space):
        assert isinstance(space,Space)
        nspace = asc_Space_NamedSpace()
        nspace.cSpace = space        
        nspace.cName  = name  
        # repo_NamedSpace.create(nspace)
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
    
    @classmethod
    def place_on_disk(cls,space,dp):
        ''' Place space on disk at directory path. If folder exists, throw error'''
        #TODO

class repo_Export(repo_interface_base):
    base=Export

    @classmethod
    def from_space(cls, space, hid, place=False, export_dp=None, user=None, session=None)->Export:
        user,session = cls.db_interface.fill_context(User=user, Session=session)

        dbi = cls.db_interface
        print('Session',dbi.c_session.get())
        print('User'   ,user)

        export = cls.base()

        export.hid       = hid
        export.myUser    = user
        export.mySession = session
        export.mySpace   = space
        export.onDisk    = False

        if export_dp:
            export.location = export_dp
        else:
            with cls.db_interface.repo_cm(Export=export,Space=space):
                export.location = cls.db_interface.settings.database.filepaths.export

        if place:
            cls.place_on_disk(export)

        return export
    
    @classmethod
    def place_on_disk(cls,export)->None:
        _repo_Space = cls.db_interface.repo_Space
        _repo_Space.place_on_disk(export.mySpace, export.location)
        cls.modify(export,onDisk=True)

class repo_Session(repo_interface_base):
    base=Session

    @classmethod
    def make(cls,hid,user:User):        

        session_inst = cls.base()
        session_inst.hid    = hid
        session_inst.myUser = user
                
        return session_inst
    

class context():
    File    = ContextVar('File'   , default=None)
    Space   = ContextVar('Space'  , default=None)
    Export  = ContextVar('Export' , default=None)
    Session = ContextVar('Session', default=None)
    User    = ContextVar('User'   , default=None)
    
    @classproperty
    def root_dir(cls):
        db_path = cls.db_path.get().get()
        if db_path.startswith(':'):
            return cls._db_root_fallback.get().get()
        else:
            return os.path.split(db_path)[0]

    @classproperty
    def user(cls): return cls.User.get().id
    
    @classproperty
    def session(cls): return cls.Session.get().id
        
    @classproperty
    def view(cls): return cls.View.get().hid
    
    @classproperty
    def export(cls): return cls.Export.get().hid

    @classproperty
    def f_uuid(cls): return cls.File.get().id
    @classproperty
    def f_uuid_s(cls): return cls.File.get().id[:10]

    @classproperty
    def s_uuid(cls): return cls.Space.get().id
    @classproperty
    def s_uuid_s(cls): return cls.Space.get().id[:10]

    @classproperty
    def v_uuid(cls): return cls.View.get().id
    @classproperty
    def v_uuid_s(cls): return cls.View.get().id[:10]

    @classproperty
    def e_uuid(cls): return cls.Export.get().id
    @classproperty
    def e_uuid_s(cls): return cls.Export.get().id[:10]
    