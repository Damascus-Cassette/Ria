from contextvars import ContextVar

Backwards_Context = ContextVar('Backwards_Context', default = None)

foreign_cache_dir = ContextVar('foreign_cache_dir', default = None)
local_cache_dir   = ContextVar('local_cache_dir', default = None)
local_temp_dir    = ContextVar('local_temp_dir', default = None)


CACHE = ContextVar('GLOBAL_CACHE',default=None)
    #Current operating cache, independant of datastruct.