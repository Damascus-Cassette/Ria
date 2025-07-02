from typing import Any
from contextvars import ContextVar
from contextlib  import contextmanager
from .settings_base import _context_variable_base, _settings_base
from .settings_base import formatted_string as fs
from .settings_base import formatted_path   as ffp

class _context:
    #Standin, replaced on import.
    ...

class platform_context_variable(_context_variable_base):
    Context = _context
    _strict = False

    _c_attr = 'platform'
    _d_attr = 'default'
    _keys   = ['default','windows','linux']

    default : ffp = ffp('./face_default/')
    windows : ffp = ffp('./face_win')
    linux   : ffp = ffp('./face_lin')

pcv = platform_context_variable

class db_info_dirs(_settings_base):
    Context = _context
    _strict = False

    view   : ffp = ffp("./views")
    store  : ffp = ffp("./store")
    export : ffp = ffp("./export")
    logs   : ffp = ffp("./log/{type}")

class db_info_filepaths(_settings_base):
    _strict = False
    Context = _context
    view            : ffp = ffp("{user}/{session}/{uuid_short}/{uuid}")
    view_log        : ffp = ffp("{user}/{session}/{uuid_short}/{uuid}.log")

    store           : ffp = ffp("{uuid_short}/{uuid}.blob")
    store_log       : ffp = ffp("{uuid_short}/{uuid}.log")

    export          : ffp = ffp("{user}/{session}/exports/{uuid}/")
    export_log      : ffp = ffp("{user}/{session}/exports/{uuid}.log")
    export_junction : ffp = ffp("{user}/{session}/exports/{name}/" )

class db_info_timeout(_settings_base):
    _strict = False
    ''' Timeout after 0 Summed users per object type (views do not count innactive sessions)'''
    Context = _context
    file   : str = "0h00m"
    space  : str = "0h00m"
    
    view   : str = "24h00m"
    export : str = "24h00m"

class db_info(_settings_base):
    add_to_context = ['db_standard','db_root']
    _strict         = False
    context        = _context
    
    db_standard: str = 'sqlite'
    db_root    : str = ':memory:'
    db_path    : ffp = ffp("{db_standard}:///{db_root}")

    dirs       : db_info_dirs      = db_info_dirs()
    filepaths  : db_info_filepaths = db_info_filepaths()
    timeout    : db_info_timeout   = db_info_timeout()
    
    # facing_dir : pcv = pcv({'windows':'./face_win/','linux':'./face_linux/'})    #converted on import


class manager_services(_settings_base):
    ''' Generic Services '''
    _strict = False
    Context = _context
    cleanup_period : str  = '12h00m'
    verify_files   : bool = True

class manager_info(_settings_base):
    ''' All info related to running this module as a serivce.'''
    _strict = False
    
    services         : manager_services = manager_services()
    
    debug_standalone : bool = False
    debug_port       : str  = 3001

    port             : int  = 3001
    require_subuser  : bool = False

class client_info(_settings_base):
    _strict = False
    debug_standalone : bool = False
    debug_manager    : str  = "localhost:3001"

    manager_address  : str  = ''

class settings_interface(_settings_base):
    _strict = False
    database : db_info      = db_info()
    manager  : manager_info = manager_info()
    client   : client_info  = client_info()

if __name__ == '__main__':
    import argparse
    import pprint
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file')
    parser.add_argument('-e', '--export',default=False,action='store_true')
    args = parser.parse_args()
    
    settings = settings_interface()
    if not args.export:
        settings.load_file(args.file)
        pprint.pprint(settings.export_dict_recur())
    if args.export:
        settings.save_file(args.file,overwrite=True,export_defaults=True)

