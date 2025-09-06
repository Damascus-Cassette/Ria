from .Env_Variables import (working_dir, temp_dir, foreign_cache_dir)

from contextlib import contextmanager

from contextvars import ContextVar

current_env = ContextVar('current_env', default = None)

from types import LambdaType

import os
from pathlib import Path

import shutil

@contextmanager
def temp_env(self,state_key,**kwargs):
    directory = os.path.join(Path(temp_dir.get()), state_key)
    directory = Path(directory)
    with Node_File_Env(str(directory.absolute()),**kwargs) as cwd:
        yield cwd
    
@contextmanager
def caching_env(state_key,**kwargs):
    directory = os.path.join(Path(working_dir.get()), state_key)
    directory = Path(directory)
    with Node_File_Env(directory.absolute(),**kwargs) as cwd:
        yield cwd


class Node_File_Env():
    ''' temprary shallow representation of a file directory that ensures directory exists, gives a few extra controls like inload, incopy, lock/unlock, ect. 
    Also for the session it tracks from and to directory to allow easier spacial transform, ie  `self.inlink(foreign_a) ; local_a = self[foreign_a]` 
    '''
    
    directory_path : Path

    mapping : dict
        #Temp mapping for prev abs -> current directory

    def __init__(self, directory_path:str|Path, /, inload_paths:tuple = tuple(), incopy_paths:tuple = tuple()):
        ''' create directory path w/a, otherwise just load it '''
        assert isinstance(directory_path, (str, Path))

        dp = Path(directory_path)
        os.makedirs(dp, exist_ok=True)
        self.directory_path = dp
        
        self.mapping = {}

        self.inload(*inload_paths)
        self.incopy(*incopy_paths)


    def __str__(self):
        ''' Used in actual loading of a path'''
        return str(self.directory_path)


    def inload(self,*paths:tuple[str]):
        ''' Inload all paths to symlinks. Keeps names and assume link to cwd root, 
        To specify from/to dirs use inload_mapping '''

        for path in paths:
            res_path = os.path.join(str(self.directory_path), os.path.split(str(path))[-1])
            print('SELFPATH:', self.directory_path)
            print('SOURCEPATH', path)
            print('SOURCECUT', os.path.split(str(path))[-1])
            print('RESPATH:', res_path)
            self.link(Path(path), str(res_path))

    
    def inload_mapping(self,path_mapping):
        ''' inload a dict of {from : to}, which allows paths relative to current working dir'''
        
        for k,v in path_mapping:
            if str(v).startswith('.'):
                v = os.path.join(self.directory_path, str(v)[1:])    
            assert self.is_subdir(v)
            self.link(k,v)


    def incopy(self,*paths):
        ''' Inload all links to symlinks, localize as true instead copies '''

        for path in paths:
            path = Path(path)
            self.copy(path, os.path.join(self.directory_path, path.split()[-1]))


    def incopy_mapping(self, path_mapping):
        ''' copy a dict of {from : to}, which allows paths relative to current working dir'''

        for k,v in path_mapping:
            if str(v).startswith('.'):
                v = os.path.join(self.directory_path, str(v)[1:])    
            assert self.is_sub(v)
            self.link(k,v)


    def link(self,from_path:Path, to_path:Path):
        ''' Create a junction or symllink between two files '''
        if Path(from_path).is_dir():
            shutil.copytree(src=from_path, dst=to_path, symlinks=True)
        else:
            Path(from_path).symlink_to(target=to_path, target_is_directory=from_path.is_dir())


    def copy(self, from_path:Path, to_path:Path):
        ''' Create a junction or symllink between two files '''
        if from_path.is_dir():
            shutil.copytree(from_path, to_path, symlinks=False)
        else:
            shutil.copy2(from_path, to_path,follow_symlinks=True)
        
    def make_local(self,path:Path):
        assert self.is_sub(path)
        if path.is_symlink() or path.is_junction():
            shutil.copy2(path,path,follow_symlinks=True)

    def localize(self,*paths):
        ''' copy-local of directories. Must be in cwd. Discouraged generally. '''
        for path in paths:
            self.localize(path)

    def localize_recur(self, dirs, depth = -1):
        ''' copy-local of directories passed in recursive, must be in cwd default is unconstrained localize '''
        for x in dirs:
            origin = Path(x).resolve()
            shutil.copytree(origin, x, symlinks=False)
        
    def __enter__(self,):
        self.unlock()
        return self

    def __exit__(self,*args,**kwargs):
        self.lock()


    def is_sub(self,path:Path):
        ''' check if path is subdirectory to self's path. Does not resolve relative '''
        os.path.commonprefix(self.directory_path.resolve(),path.resolve())


    def __getitem__(self,dir):
        ''' dir coming from extern and quirying mapping, or being relaitve to self root for absolute '''
        if str(dir).startswith('.'):
            return os.path.join(self.directory_path, dir[1:])
        
        if str(dir) in self.mapping.keys():
            return self.mapping[str(dir)]
        
        return NotImplementedError('TODO: Search mapped subdirectories')
        

    # def __iter__(self):
    #     ''' Iter over files & folders '''
    #     ...

    # def items(self,folders:bool=True, files: bool=True,filter:LambdaType=None):
    #     ''' Iter over folder & fp key sets '''

    # def contents_uuid


    def unlock(self,):
        ''' Set so all files in self can be edited '''
        os.chmod(self.directory_path,777,follow_symlinks=False)
        

    def lock(self,):
        ''' Set so all files in self cannot be edited '''
        os.chmod(self.directory_path,555,follow_symlinks=False)
        


class node():
    
    # @hook_trigger('execute')
    def execute(self,):
        a = self.in_socket[0].execute()

        self.asc_key(a, self.local_state)
        yield self.cache_search(a , self.local_state, future_asc = True)

        with caching_env(self.state_key, copy_paths = (a,)) as cwd:
            ...
            # do_shit(cwd[a]) and asc with self #Local dir
