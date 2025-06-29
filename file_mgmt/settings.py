from typing import Any
from contextvars import ContextVar
from contextlib  import contextmanager
from .settings_base import _context_variable_base, _settings_base

class context:
    #Fugly structure, consider something cleaner
    platform : ContextVar = ContextVar('platform',default = 'default') 


@contextmanager
def settings_context(**kwargs):
    tokens = {}
    try:
        for k,v in kwargs.items():
            if (cvar:=getattr(context,k,None)):
                tokens[k] = cvar.set(v)
            else:
                raise Exception(f"Context could not be set for key {k} of value {v}")
            yield
    finally:
        for k,v in tokens.items():
            cvar = getattr(context,k,None)
            cvar.reset(v)


class platform_context_variable(_context_variable_base):
    context = context
    _c_attr = 'platform'
    _d_attr = 'default'
    _keys   = ['default','windows','linux']

    default = './face_default/'
    windows : str
    linux   : str

pcv = platform_context_variable

class db_info(_settings_base):
    context = context
    database_fp   : str
    cache_dir     : str = './cache/'
    logging_dir   : str = './logs/'
    lock_location : str = './'
    facing_dir    : pcv = pcv({'windows':'./face_win/','linux':'./face_linux/'})    #converted on import

class settings_interface(_settings_base):
    context = context
    strict = False
    database : db_info = db_info()


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

