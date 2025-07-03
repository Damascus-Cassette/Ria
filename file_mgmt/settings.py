from .settings_base import settings_dict_base, input_base, input_context_formatted

import string

class input_context_platform(input_base):
    def return_data(self):
        key = self.context.platform.get()
        if key in self.data.keys():
            value = self.data[key]
        else:
            value = self.data['default']

        return self.string_format_from_context(value,self.context)


class input_context_format_path(input_base):
    strict = False
    def return_data(self):
        if self.data.startswith('./'):
            value = '{db_path}'+self.data[1:]
        elif self.data.startswith('../'):
            value = '{db_path}/'+self.data        
        else:
            value = self.data

        return self.string_format_from_context(value,self.context)

i_g   = input_base.construct
i_f   = input_context_formatted.construct
i_fp  = input_context_format_path.construct
i_pcv = input_context_platform.construct


##################################


class settings_interface(settings_dict_base):
    _strict = False
    _in_context = 'Settings_Root'

    class _tests(settings_dict_base):
        #Control class for testing
        _strict   = False
        _required = False

        context_vars = {
            'db_standard': 'db_standard',
            'db_path'    : 'db_path'    ,
            'user'       : 'user'       ,
            'user'       : 'user'       ,
            'session'    : 'session'    ,
            'uuid_short' : 'uuid_short' ,
            'uuid'       : 'uuid'       ,
            }
        
        test_a        = i_fp(str,default="./{user}/{session}/{uuid_short}/{uuid}.log")
        control_a     = "db_path/user/session/uuid_short/uuid.log"
        
        test_b        = i_fp(str,default="../{user}/{session}/{uuid_short}/{uuid}.log")
        control_b     = "db_path/../user/session/uuid_short/uuid.log"

    class client_info(settings_dict_base):
        _strict = False
        _required = False
        
        address  : str  = i_g(str, default = 'localhost:3001')

    class manager(settings_dict_base):
        ''' All info related to running this module as a serivce.'''
        _strict = False
        _required = False

        port             : int  = i_g(int ,default=3001)
        require_subuser  : bool = i_g(bool,False)
        
        class services(settings_dict_base):
            ''' Generic Services '''
            _strict = False
            _required = False

            cleanup_period : str  = i_g(str , default='12h00m')
            verify_files   : bool = i_g(bool, default=True)

    class database(settings_dict_base):
        _strict = False
        _required = False

        db_standard    = i_g(str,  in_context='db_standard' , default = 'sqlite')
        db_path        = i_g(str,  in_context='db_path'     , default = ':memory:')
        _sqla_db_path  = i_fp(str, default = "{db_standard}:///{db_path}")

        class dirs(settings_dict_base):
            _strict = False
            _required = False

            view   = i_fp(str, default="./views")
            store  = i_fp(str, default="./store")
            export = i_fp(str, default="./export")
            logs   = i_fp(str, default="./log/{type}")

        class filepaths(settings_dict_base):
            _strict = False
            _required = False

            view            = i_fp(str,default="{user}/{session}/{v_uuid_s}/{v_uuid}")
            view_log        = i_fp(str,default="{user}/{session}/{v_uuid_s}/{v_uuid}.log")

            store           = i_fp(str,default="{f_uuid_s}/{f_uuid}.blob")
            store_log       = i_fp(str,default="{f_uuid_s}/{f_uuid}.log")

            export          = i_fp(str,default="{user}/{session}/exports/{e_uuid}/")
            export_log      = i_fp(str,default="{user}/{session}/exports/{e_uuid}.log")
            export_junction = i_fp(str,default="{user}/{session}/exports/{export}/" )

        class timeout(settings_dict_base):
            _strict = False
            _required = False

            file   = i_g(str,default="0h00m")
            space  = i_g(str,default="0h00m")
            
            view   = i_g(str,default="24h00m")
            export = i_g(str,default="24h00m")
