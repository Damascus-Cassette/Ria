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
    return os.path.join(this_dir,'test_resouces/test_subject_file.txt')

@pytest.fixture
def test_dp():
    this_dir = os.path.split(__file__)[0]
    return os.path.join(this_dir,'test_resouces/test_space')

@pytest.fixture
def dbi(db_fp):
    return db_interface({'database':{'db_path':db_fp}})

def test_import(dbi):
    print(dbi)

def test_file_space_creation(dbi,test_fp):
    
    user        = dbi.repo_user.make('TestUser','TestUser')
    session     = dbi.repo_Session.make('TestSession','TestSession',user)
    session.hid = 'TestSession'

    with dbi.repo_cm(user=user, session=session):
        space = dbi.repo_Space.base()
        named_file = dbi.repo_NamedFile.store(filepath     = test_fp,
                                            filename     = os.path.split(test_fp)[1],
                                            space        = space,
                                            repl_symlink = False,
                                            do_remove    = False)
        space.files.append(named_file)
        dbi.repo_Space.set_id(space)
        dbi.repo_Space.create(space)

        nSpace = dbi.repo_Space.as_named(space,'NamedSpace')

        export = session.export_space(space)
        export = session.export_namedSpace(nSpace)
