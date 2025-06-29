from ..db_interface import db_interface 
from ..settings import settings_interface

import os 
import pytest

def malformed_settings():
    this_dir = os.path.split(__file__)[0]
    return os.path.join(this_dir,'test_resources/malformed_settings.yaml')

def good_settings():
    this_dir = os.path.split(__file__)[0]
    return os.path.join(this_dir,'test_resources/test_settings.yaml')

@pytest.mark.parametrize('path, expected',
        [
            (malformed_settings(), False),
            (good_settings(), True)
        ])
def test_settings(path,expected):
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