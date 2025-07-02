import pytest

from ..settings_base import input_base, input_context_formatted, settings_dict_base
from ..settings  import settings_interface

i_f = input_context_formatted.construct
i_g = input_base.construct

@pytest.fixture
def test_settings_struct():
    class test(settings_dict_base):

        var1 : str = i_g(str, in_context='var_a', default='Var1Contents')
        var2 : str = i_f(str, in_context='var_b', default='{var1}_DefaultString2')

        class nested(settings_dict_base):
            # def __init__(self, data):
            #     print(data)
            #     raise Exception('FUCK')
            var3 : str = i_f(str, in_context='var3')

    return test

@pytest.fixture
def test_settings_data_good():
    return {
        'var1'   : 'var1Contents',
        'var2'   : 'var2Contents',
        'nested' : {
            'var3' : '{var_a}{var_b}'
        }
    }

# @pytest.fixture
# def settings(test_settings_struct,test_settings_data_good):

def test_settings(test_settings_struct:settings_dict_base,test_settings_data_good):
    settings = test_settings_struct.load_data(test_settings_data_good)
    d = test_settings_data_good
    c = settings.context    

    print(c.var_a)
    print(c.var_a.get())

    c_var_a = c.var_a.get()
    c_var_b = c.var_b.get()

    assert c_var_a.get() == d['var1']
    assert c_var_b.get() == d['var2']
    
    d_var_a = settings.var1
    d_var_b = settings.var2

    assert d_var_a == d['var1']
    assert d_var_b == d['var2']
    
    assert settings.nested.var3  == 'var1Contents'+'var2Contents'
    assert settings.nested.var3  ==  c.var_a.get().get() + c.var_b.get().get() 
    assert settings.nested.var3  ==  c.var3.get().get()

@pytest.fixture
def full_settings_data():
    return {}

def test_settings_full(full_settings_data:dict):
    settings = settings_interface.load_data(full_settings_data)
    with settings.generic_cm(**settings._tests.context_vars, construct = True):
        assert settings._tests.test_a == settings._tests.control_a
        assert settings._tests.test_b == settings._tests.control_b