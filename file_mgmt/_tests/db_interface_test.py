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
    return db_interface({'database':{'db_path':db_fp}})

def test_import(dbi):
    print(dbi)

def test_file_space_export_creation(dbi,test_fp):
    with dbi.session_cm():
        print(dbi.c_session.get())

        user        = dbi.repo_user.make(id='TestUser', hid='TestUser')
        dbi.repo_user.create(user)

        session     = dbi.repo_Session.make(hid='TestSession', user=user)
        dbi.repo_Session.create(session)

        with dbi.repo_cm(User=user, Session=session):
            space = dbi.repo_Space.base()
            named_file = dbi.repo_NamedFile.store(filepath     = test_fp,
                                                filename     = os.path.split(test_fp)[1],
                                                space        = None,
                                                repl_symlink = False,
                                                do_remove    = False)
            space.myFiles.append(named_file)

            dbi.repo_Space.set_id(space)
            # dbi.repo_Space.create(space)
            # dbi.repo_NamedFile.create(named_file) #implicity created in space create?

            export = dbi.repo_Export.from_space(space, hid='ExportName')
            dbi.repo_Export.create(export)

            # dbi.repo_NamedFile.create(named_file)
                # commit(space) implicitly commits myFiles. SO this throws errors
                # space.myFiles
            
            # space.myFiles.append(named_file)

            # nSpace = dbi.repo_Space.as_named(space,'NamedSpace')

            # export = session.export_namedSpace(nSpace)
