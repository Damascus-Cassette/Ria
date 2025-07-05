from ..settings     import settings_interface
from ..db_interface import db_interface
import os
import pytest

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
    with dbi.session_cm():
        user        = dbi.repo_user.make(id='TestUser', hid='TestUser')
        dbi.repo_user.create(user)

        session     = dbi.repo_Session.make(hid='TestSession', user=user)
        dbi.repo_Session.create(session)
    dbi.context.Session.set(session)
    dbi.context.User.set(user)
    return dbi

def test_file_space_export_creation(dbi,test_fp):
    with dbi.session_cm(commit = False):
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


def test_usercounts(dbi:db_interface):
    with dbi.session_cm(commit = False):
        space      = dbi.repo_Space.base()

        file       = dbi.repo_File.base()
        file.id    = 'RandomID_Standin'

        named_file = dbi.repo_NamedFile.base()
        named_file.cName  = 'NamedFile.txt'
        named_file.cFile  = file
        named_file.pSpace = space

        dbi.repo_Space.set_id(space)

        file.get_alive_users()

        assert not file.cached_users
        assert not file.hasUsers

        assert not space.hasUsers
        assert not space.inDecay
        assert not space.firstFileDrop

        export = dbi.repo_Export.from_space(space, hid='ExportName')
        # dbi.repo_Export.create(export)
        file.get_alive_users()

        assert file.cached_users
        assert file.hasUsers

        assert space.cached_users
        assert space.hasUsers


