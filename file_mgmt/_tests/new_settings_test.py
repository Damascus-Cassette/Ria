import pytest

from ..settings_new import input_base, input_context_formatted, settings_dict_base

i_f = input_context_formatted.construct
i_g = input_base.construct

@pytest.fixture
def settings_struct():
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
def settings_data_good():
    return {
        'var1'   : 'var1Contents',
        'var2'   : 'var2Contents',
        'nested' : {
            'var3' : '{var_a}{var_b}'
        }
    }

# @pytest.fixture
# def settings(settings_struct,settings_data_good):

def test_settings(settings_struct:settings_dict_base,settings_data_good):
    settings = settings_struct.load_data(settings_data_good)
    d = settings_data_good
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