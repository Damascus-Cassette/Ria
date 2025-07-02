from ..db_interface  import db_interface,settings_interface
import pytest
import os

this_dir        =  os.path.split(__file__)[0]
good_settings   =  os.path.join(this_dir,'test_resources/test_settings.yaml')
test_resources  =  os.path.join(this_dir,'test_resources')

@pytest.fixture(scope="session")
def _test_dir(pytestconfig):
    return pytestconfig.getoption("test_dir")

@pytest.fixture
def _settings(_test_dir):
    s = settings_interface()
    s.load_file(good_settings)
    return s

@pytest.fixture
def _db_interface():
    return db_interface(good_settings) 


#################################################################################
###                                                                           ###       
#################################################################################


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

def test_session_basic(_db_interface:db_interface):
    repo_user = _db_interface.repo_user
    with _db_interface.session_cm() as session:
        u1 = repo_user.base()
        u1.id  = 'IDname1'
        
        u2 = repo_user.base()
        u2.id  = 'IDname2'
        
        u3 = repo_user.base()
        u3.id  = 'IDname3'
        
        session.add(u1)

        repo_user.create(u2)

        _savepoint = session.begin_nested()  # establish a savepoint
        session.add(u3)
        _savepoint.rollback() 

        assert     session.query(repo_user.base).filter_by(id='IDname1').all()
        assert     session.query(repo_user.base).filter_by(id='IDname2').all()
        assert not session.query(repo_user.base).filter_by(id='IDname3').all()

        repo_user.delete(u1)
        repo_user.update(u2,id='IDname202')

        assert not session.query(repo_user.base).filter_by(id='IDname1').all()
        assert not session.query(repo_user.base).filter_by(id='IDname2').all()
        assert     session.query(repo_user.base).filter_by(id='IDname202').all()


def test_db_file_upload(_db_interface:db_interface):
    dbi = _db_interface

    with _db_interface.session_cm() as session:
        user = dbi.repo_user.base()
        user.id  = 'IDname1'

        session  = dbi.repo_Session.start('test_session',user)
        nSpace   = dbi.repo_NamedSpace.store(test_resources, 'test_space', repl_junction=False, do_remove=False)
        
        nSpace.session_export(session, dp = ) #Default datapath should be relevent to function & store path in yaml
        nSpace.session_view(session,   dp = ) #
        nSpace.user_export(user,       dp = ) #

        assert nSpace.total_users == 3

        session.close()
        assert nSpace.total_users == 2

        session.exports.clear()
        assert nSpace.total_users == 1

        user.exports.clear()
        assert nSpace.total_users == 0


# def test_db_space_upload():
#     ...

# def test_db_userrepo(_db_interface:db_interface):
#     cls = _db_interface.user_repo
#     with _db_interface.session_cm() as session:
#         # session == cls.c_session.get()
#         obj = cls.base()
#         obj.id  = 'IDname'
#         obj.hid = 'WrongName'
        
#         print(obj)
#         obj = cls.create(obj)
#         print(obj)

#         assert not session.query(cls.base).filter_by(hid='RightName').all()
        
#         cls.update(obj,hid='Rightname')
#         session.refresh(obj)

#         assert session.query(cls.base).filter_by(hid='RightName').all()
    
#     # cls.c_session.get().close()