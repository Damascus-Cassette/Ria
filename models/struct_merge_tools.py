''' Merging items memo & tools, for when a|b needs c.ref -> a
May change to delayed world reference replacement, odd topic.
'''


from contextvars import ContextVar
from contextlib  import contextmanager

from functools import wraps

merge_memo = ContextVar('struct_merge_memo',default=None)

@contextmanager
def merge_context():
    t = None
    if not merge_memo.get():
        t = merge_memo.set({})
    yield
    if t:
        merge_memo.reset(t)

def merge_wrapper(func):
    @wraps
    def Func(*args,**kwargs):
        return func(*args,**kwargs)
    return Func
