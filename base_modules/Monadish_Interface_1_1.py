''' Atomic focused rewrite to monadish, with testing of each indivdual action '''

from ..models.struct_module import module, module_test
from ..models.base_node     import socket_group
from .Execution_Types       import _mixin, item
# from .Execution_Types       import socket_shapes as st

from typing                 import Any, Self, TypeAlias,AnyStr,Type
from types                  import FunctionType
from inspect                import isclass


class utils:
    def iter_unseen(*iterables):
        seen = []
        for iterable in iterables:
            for x in iterable:
                if not (x in seen):
                    yield x


class main(module):
    ''' A monad-like interface for creating graphs'''
    UID     = 'Monadish_Interface'
    Version = '1.0'

############ CLASSES ############



class socket_group_mixin(_mixin.socket_group):
    # def Shape as class method??
    #TODO: Make work in the class as well
    
    @staticmethod
    def shape(self_or_cls:Self,is_left=False)->tuple[tuple[Any],int]:
        ''' If is_left, return actual tuple, else as any '''
        ''' Next check in this module make inst and have return func to connect '''
        if isclass(self_or_cls): return self_or_cls._inst_shape(is_left = is_left)
        else:                    return self_or_cls._inst_shape(is_left = is_left)
    
    @classmethod
    def _cls_shape(cls,is_left=False):
        ...
    def _inst_shape(self,is_left=False):
        ...

############ NODES ############

class new_socket(item.socket):
    Module     = main 
    UID        = 'Test_MonadishSocket'
    Version    = '1.0'
    Label      = 'Test_MonadishSocket'
    Desc       = ''' Test String Socket '''

    Value_Type    = str
    Value_Default = 'c'
    
class left_example(item.exec_node):
    Module  = main 
    UID     = 'Monadish_Left_Example'
    Label   = 'Monadish_Left_Example'
    Version = '1.0'

    in_sockets    = [socket_group.construct('set_a', Sockets=[new_socket])]
    out_sockets   = [socket_group.construct('set_a', Sockets=[new_socket])]
    side_sockets  = [socket_group.construct('set_a', Sockets=[new_socket])]

class right_example(left_example):
    UID     = 'Monadish_Right_Example'
    Label   = 'Monadish_Right_Example'

main._loader_items_ = [new_socket, left_example,right_example]

############ TESTS ############


def try_connect_manual(subgraph,left,right):
    print(left.in_sockets.groups)

    lg = left.in_sockets.groups[0]
    rg = right.in_sockets.groups[0]    

    lg_shape = lg.shape(is_left=True)
    rg_shape = rg.shape()

    print(lg_shape)
    print(rg_shape)
    raise Exception()

def test_connection_1(graph,subgraph):
    with subgraph.context.Cached():
        left  = left_example(default_sockets=True)
        right = right_example(default_sockets=True)
        try_connect_manual(subgraph,left,right)
        


main._module_tests_.append(module_test('TestA',
                module      = main,
                module_iten = {main.UID : main.Version,
                               'Core_Execution':'2.0'}, 
                funcs       = [test_connection_1],
                ))