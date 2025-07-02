from ..settings     import settings_interface
from ..db_interface import db_interface
import pytest

@pytest.fixture
def dbi():
    return db_interface({})

def test_import(dbi):
    print(dbi)