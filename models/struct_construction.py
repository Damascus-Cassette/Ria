
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
    _constr_join_dicts_ : list[str]
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
            
            if (k:=getattr(cls,'_constr_bases_key_',None)) is not None:
                
                other_bases = Bases.get()[k]


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

            else: 
                other_bases = []
            

            new_lists = {}
            new_dicts = {}
            for k in getattr(cls,'_constr_join_lists_',[]):
                new_lists[k]=[]
                for x in other_bases:
                    new_lists[k].extend(getattr(x,k,[]))

            for k in getattr(cls,'_constr_join_dicts_',[]):
                new_dicts[k]={}
                for x in other_bases:
                    if val := getattr(x,k,{}):
                        new_dicts[k] = new_dicts[k] | val

            if getattr(cls,'_constr_in_place_',False):
                new_tuple = tuple(other_bases) + cls.__bases__ 
                new_tuple = tuple([x for x in new_tuple if x is not object])
                     #Object in the middle of the inheritance causes MRO error

                try:
                    cls.__bases__ = new_tuple
                    for k,v in new_lists.items():
                        setattr(cls,k,v)
                    new_type = cls
                except:
                    print(cls)
                    print('Original:', cls.__bases__)
                    print('Mixins:  ', other_bases)
                    print('Resolve to attempt:', new_tuple)
                    print(new_tuple[0].__bases__[0])
                    # for x in new_tuple:
                    #     print(x.__qualname__,'BASES:',x.__bases__)
                    raise
            
            else:
                new_type = type('Constr_'+cls.__name__,
                                (cls, *other_bases),
                                new_dicts|new_lists|{'_constr_has_run_':True})
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


