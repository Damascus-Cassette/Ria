import pytest
import os

this_dir           = os.path.split(__file__)[0]
good_settings      = os.path.join(this_dir,'test_resources/test_settings.yaml')

from .._test_db_interface  import db_interface,settings_interface

@pytest.fixture
def _settings():
    s = settings_interface()
    s.load_file(good_settings)
    return s

@pytest.fixture
def _db_interface():
    return db_interface(good_settings) 

@pytest.mark.parametrize('attr,value,expects,succeed',[
    ('platform','linux','linux',True),    
    ('platform','windows','windows',True),    
    ('__not_context__','windows','windows',False),    
])
def test_db_interface_context_echo(_db_interface:db_interface,attr,value,expects,succeed:bool ):

    with _db_interface.generic_cm(**{attr:value}):
        try:
            ret = _db_interface._repo_base.echo_context(attr)
        except:
            ret = False

        if not (ret == expects) == succeed:
            raise Exception(f'Context Echo Failed! Key:{attr} Expected:{value} Got:{ret}')

@pytest.mark.parametrize('attr,value,expects,succeed',[
    ('platform'        , 'default', './face_default/' , True  ),    
    ('platform'        , 'linux'  , './face_linux/'   , True  ),    
    ('platform'        , 'windows', './face_win/'     , True  ),    
    ('platform'        , 'linux'  , 'Anthing'         , False ),    
    ('platform'        , 'windows', 'Anthing'         , False ),    
    ('__not_context__' , 'windows', 'Anything'        , False ),    
])
def test_db_settings_context_echo(_db_interface:db_interface,attr,value,expects,succeed:bool ):

    with _db_interface.generic_cm(**{attr:value}):
        try:
            ret = _db_interface.settings.database.facing_dir.get()
        except:
            ret = False

        if not (ret == expects) == succeed:
            raise Exception(f'Context Echo Failed! Key:{attr} Expected:{value} Got:{ret}')

def test_db_userrepo(_db_interface:db_interface):
    cls = _db_interface.user_repo
    with _db_interface.session_cm() as session:
        # session == cls.c_session.get()
        obj = cls.base()
        obj.id  = 'IDname'
        obj.hid = 'Rightname'
        cls.create(obj)
        # print(obj)
        assert not session.query(cls.base).filter_by(hid='RightName').all()
        cls.update(obj,hid='Rightname')
        assert session.query(cls.base).filter_by(hid='RightName').all()