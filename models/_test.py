from typing import Generic, TypeVarTuple, get_args
from types import GenericAlias

T = TypeVarTuple("T")

class Base(Generic[*T]):
    values: tuple[*T]
    type_T: tuple[type,...]

    def __init_subclass__(cls)->None:
        cls.type_T = get_args(cls.__orig_bases__[0])


class example2(Base[int,'str']):
    ...


print(get_args(Base[str,'int'])[-1].__forward_arg__)


print(Base[int,str])
print(Base[int,str].__class__.__bases__)
print(isinstance(Base[int,str],GenericAlias))