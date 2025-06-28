
# Contains types that define the db repo pattern
from contextlib import contextmanager

@contextmanager
def transaction(func):
    @wraps(func)
    def func():
        ...
    return func



class meta_transactional():
    ''' Construction of a new class to inherit that auto-wraps '''
    def __new__(cls,types:tuple,attrs:dict):
        ...
    
    def _wrap_transactions():
        ...