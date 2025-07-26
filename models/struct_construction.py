
## Construction base inherited into node struct.
## Plan is 
## - allow context varaibles to supply other (bases) for the constructed class
## - repace 1st level references & annotations
## - Add to new dict with original class as key
    ## Will be used in the loader to replace module references on a deepcopy of the module??.

from contextvars import ContextVar
from contextlib  import contextmanager
from inspect import isclass
from typing import Any,Self

class _bases(dict):
    def __missing__(self,k):
        res = self[k] = ContextVar(k,default=[]) 
Bases       = ContextVar('Constr_Bases', default = None) 
Constructed = ContextVar('Constructed' , default = None)

@contextmanager
def ensure_bases(reset=True):
    t = None
    if Bases.get() is None:
        t = Bases.set(_bases)
    yield t
    if t and reset:
        Bases.reset(t)

@contextmanager
def ensure_constructed(reset=True):
    t = None
    if Constructed.get() is None:
        t = Constructed.set({})
    yield
    if t and reset:
        Constructed.reset(t)

class ConstrBase():
    _constr_whitelist_  : list[str]
    _constr_bases_key_  : str
    _constr_join_lists_ : list[str]
    _constr_call_post_  : list[str]

    _constr_has_run_   : bool = False
    _constr_in_place_  : bool = True

    _constr_asbase_discard_ : bool


    @classmethod
    def Construct(cls,recur=True)->Self:
        with ensure_bases() and ensure_constructed():
            if getattr(cls,'_constr_has_run_',False):
                return cls
            elif cls in Constructed.get().keys():
                return Constructed.get()[cls]
            
            if k:=getattr(cls,'_constr_bases_key_',None):
                
                other_bases = Bases.get()[k]

                print(f'SOURCE BASES OF {k} ARE = {other_bases}')

                temp = type('temp', tuple(other_bases), {})
                other_bases = list(temp.__bases__) 
                other_bases = [x for x in other_bases if not getattr(x,'_constr_asbase_discard_',False)]
                # Intermediate class for joining and sorting bases via pythons internal
                    #This will have to be changed to be Method Resolution Order based!!!
                    # This does not support two level inheritance
                if cls in other_bases : b.remove(cls)
                for b in cls.__bases__:
                    if b in other_bases: other_bases.remove(b)

                # Removing anything in orig classes' chain from the constr, 
                # Prevents loops
                print(f'FILTERED BASES OF {k} ARE: {other_bases}')

            else: 
                other_bases = []
            

            new_lists = {}
            for k in getattr(cls,'_constr_join_lists_',[]):
                new_lists[k]=[]
                for x in other_bases:
                    new_lists[k].extend(getattr(x,k,[]))

            if getattr(cls,'_constr_in_place_',False):
                cls.__bases__ += tuple(other_bases)
                for k,v in new_lists.items():
                    setattr(cls,k,v)
                new_type = cls
            
            else:
                new_type = type('Constr_'+cls.__name__,
                                (cls, *other_bases),
                                new_lists|{'_constr_has_run_':True})
                Constructed.get()[cls] = new_type

            if recur: new_type.Construct_Walk()

            for k in getattr(new_type,'_constr_call_post_',[]):
                if func:=getattr(new_type,k,None):
                    func()
            

            return new_type
            

    @classmethod
    def Construct_Walk(cls)->None:
        ''' Function that can be overwritten for custom walk purposes '''
        blacklist = getattr(cls,'_constr_whitelist_',[])
        
        if (a := getattr(cls,'_constr_whitelist_',None)) is not None:
            attrs = {k:getattr(cls,k) for k in a}
        else:
            attrs = vars(cls)
        
        for k,v in attrs.items():
            if k in blacklist or k.startswith('__'):
                continue
            elif not isclass(v):
                continue
            elif issubclass(v,ConstrBase):
                setattr(cls,k,v.Construct())


