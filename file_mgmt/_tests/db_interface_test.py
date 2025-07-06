from ..settings     import settings_interface
from ..db_interface import db_interface
import os
import pytest
from sqlalchemy import inspect

@pytest.fixture
def db_fp():
    this_dir = os.path.split(__file__)[0]
    return os.path.join(this_dir,'.test_loc/test_db.db')

@pytest.fixture
def test_fp():
    this_dir = os.path.split(__file__)[0]
    return os.path.join(this_dir,'test_resources/test_subject_file.txt')

@pytest.fixture
def test_dp():
    this_dir = os.path.split(__file__)[0]
    return os.path.join(this_dir,'test_resources/test_space')

@pytest.fixture
def dbi(db_fp):
    dbi = db_interface({'database':{'db_path':db_fp}})
    with dbi.session_cm() as sqla_session:
        
        from ..db_struct import User,Session

        if not (user := sqla_session.query(User).filter_by(id = 'TestUser').first()):
            user = dbi.repo_user.make(id='TestUser', hid='TestUser')
            dbi.repo_user.create(user)

        if not (session := sqla_session.query(Session).filter_by(hid = 'TestSession').first()):
            session = dbi.repo_Session.make(hid='TestSession', user=user)
            dbi.repo_Session.create(session)

        dbi.context.Session.set(session)
        dbi.context.User.set(user)
    return dbi

def test_file_space_export_creation(dbi,test_fp):
    with dbi.session_cm(commit = True):
        # with dbi.repo_cm(User=user, Session=session):
            #Already taken care of by database start and manual context setting

        space = dbi.repo_Space.base()
        named_file = dbi.repo_NamedFile.store(filepath     = test_fp,
                                            filename     = os.path.split(test_fp)[1],
                                            space        = None,
                                            repl_symlink = False,
                                            do_remove    = False)
        space.myFiles.append(named_file)

        dbi.repo_Space.set_id(space)

        export = dbi.repo_Export.from_space(space, hid='ExportName')

        dbi.repo_Export.create(export)

def test_export_space_only(dbi:db_interface):
    with dbi.session_cm(commit = True) as sqla_session:
        space      = dbi.repo_Space.base()
        dbi.repo_Space.set_id(space)

        assert not space.hasUsers

        export = dbi.repo_Export.from_space(space, hid='ExportName')
        dbi.repo_Export.create(export)

        assert space.hasUsers

        sqla_session.delete(export)
        sqla_session.flush()

        assert not space.hasUsers

def test_export_space_and_file(dbi:db_interface):
    with dbi.session_cm(commit = True) as sqla_session:

        space      = dbi.repo_Space.base()
        file       = dbi.repo_File.base()
        file.id    = 'RandomID_Standin'
        named_file = dbi.repo_NamedFile.base()
        named_file.cName  = 'NamedFile.txt'
        named_file.cFile  = file
        named_file.pSpace = space
        dbi.repo_Space.set_id(space)

        export = dbi.repo_Export.from_space(space, hid='ExportName')
        dbi.repo_Export.create(export)

        assert file.hasUsers
        assert space.hasUsers

        sqla_session.delete(export)
        sqla_session.flush()

        assert not file.hasUsers
        assert not space.hasUsers

def test_usercounts(dbi:db_interface):
    return
    with dbi.session_cm(commit = True) as sqla_session:
        space      = dbi.repo_Space.base()

        file       = dbi.repo_File.base()
        file.id    = 'RandomID_Standin'

        named_file = dbi.repo_NamedFile.base()
        named_file.cName  = 'NamedFile.txt'
        named_file.cFile  = file
        named_file.pSpace = space

        dbi.repo_Space.set_id(space)

        # file.get_alive_users()
        sqla_session.flush()
        
        assert not file.hasUsers

        assert not space.hasUsers
        assert not space.inDecay
        assert not space.firstFileDrop

        export = dbi.repo_Export.from_space(space, hid='ExportName')
        dbi.repo_Export.create(export)
        # file.get_alive_users()

        assert file.hasUsers

        assert space.hasUsers

        dbi.repo_Export.delete(export)
        sqla_session.flush()

        # file.get_alive_users()
        assert not file.hasUsers

        assert not space.hasUsers
        assert not space.inDecay
        assert not space.firstFileDrop
        
        dbi.repo_File.delete(file) #safe=False
        assert not space.hasUsers 
        assert space.inDecay
        assert space.firstFileDrop

# def test_session_isOpen_behavior():
#     ...

def test_deletion_behavior(dbi:db_interface):
    ''' Test cascade deletion behavior of both users & spaces '''
    with dbi.session_cm(commit = True) as sqla_session:
        return 
    
        user = dbi.repo_user.make(id='Deletion_TestUser', hid='Deletion_TestUser')        
        session = dbi.repo_Session.make(hid='Deletion_TestSession', user=user)

        space      = dbi.repo_Space.base()

        file       = dbi.repo_File.base()
        file.id    = 'RandomID_Standin_2'

        named_file = dbi.repo_NamedFile.base()
        named_file.cName  = 'NamedFile.txt'
        named_file.cFile  = file
        named_file.pSpace = space

        dbi.repo_Space.set_id(space)

        with dbi.repo_cm(User=user, Session=session):
            export = dbi.repo_Export.from_space(space, hid='ExportName')
            
            dbi.repo_Export.create(export)

        assert not inspect(export).deleted
        assert not inspect(session).deleted
        assert not inspect(user).deleted
        assert not inspect(named_file).deleted

        # file.get_alive_users()
        assert file.hasUsers

        # sqla_session.delete(user)
        dbi.repo_user.delete(user)
        sqla_session.flush()

        assert inspect(user).deleted
        assert inspect(session).deleted
        assert inspect(export).deleted
        assert not inspect(named_file).deleted

        # file.get_alive_users()
        assert not file.hasUsers

        assert not inspect(space).deleted
        assert not inspect(named_file).deleted
        assert not inspect(file).deleted

        dbi.repo_Space.delete(space)
        # sqla_session.delete(space)
        sqla_session.flush()

        assert inspect(space).deleted
        assert inspect(named_file).deleted
        assert not inspect(file).deleted