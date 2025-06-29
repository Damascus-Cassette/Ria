from ..db_interface import db_interface 
from ..settings import settings_interface,settings_context

import os 
import pytest

class vars():
    this_dir           = os.path.split(__file__)[0]
    malformed_settings = os.path.join(this_dir,'test_resources/malformed_settings.yaml')
    good_settings      = os.path.join(this_dir,'test_resources/test_settings.yaml')

@pytest.fixture()
def loaded_db_interface():
    return db_interface(settings_file=vars.good_settings)

@pytest.fixture()
def loaded_settings():
    v = settings_interface()
    v.load_file(vars.good_settings)
    return v
    
@pytest.mark.parametrize('path, expected',
        [
            (vars.malformed_settings, False),
            (vars.good_settings     , True ),
        ])
def test_load_settings(path,expected):
    try:
        s = settings_interface()
        s.load_file(path)
        passed_test = True
    except:
        passed_test = False
        if expected != passed_test:
            raise
    if expected != passed_test:
        raise

def test_settings_context(loaded_settings):
    assert loaded_settings.database.facing_dir.get() == './face_default/'

    with settings_context(platform = 'windows'):
        assert loaded_settings.database.facing_dir.get() == './face_win/'
    
    with settings_context(platform = 'linux'):
        assert loaded_settings.database.facing_dir.get() == './face_linux/'
    



def test_db_interface_repos(loaded_db_interface):
    print(loaded_db_interface.test)