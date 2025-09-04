
import shutil
import os
import pathlib
from pathlib import Path

from types import FunctionType


class Cache_Env():
    ''' Folder-Env to enter and work on. Typically created with Env Varaibles. Creates folder if it doesnt exist. '''
    
    def __init__(self, dp:str):
        os.makedirs(dp,exist_ok=True)
        self.dp = Path(dp)
    
    def __enter__(self):
        self.unlock()
        return self
        
    def __exit__(self,*args,**kwargs):
        self.lock()
    
    def lock(self):
        os.chmod(self.dp,555)
    
    def unlock(self):
        os.chmod(self.dp,777)
    
    def _walk(self, from_path, yield_files=False, yield_dirs=False, limiter:None|FunctionType=None):
        visited = []
        for root,dirs,files in os.walk(from_path, walk_symlinks = True):
            if isinstance(root, FunctionType):
                if limiter(root):
                    continue

            if root in visited:
                dirs[:] = []        #Set so it stops recursing       
                continue        
            else:
                visited.append(root)
            
            # root_rel = '.' + (Path(root) - Path(from_path))
            root_rel = Path(from_path).relative_to(root)
            raise NotImplementedError('HAVNT TESTED') 
                #Create root relative to original path.

            if yield_files:
                for file in files:
                    opath = os.path.join(root,file)
                    yield(opath,Path(root).absolute(), root_rel, file)

            if yield_dirs:
                for _dir in dirs:
                    opath = os.path.join(root,dir)
                    yield(opath,Path(root).absolute(), root_rel, _dir)
                

    def link(self,from_path, to_path, keep_empty_folders = False):
        '''Copies folders and links contents. Input can be dir or fp. Does not hold onto empty folders by default.'''
        if Path(from_path).is_dir():
            for opath, root, rel, file in self._walk(from_path, yield_files=True, yield_dirs=False):
                local_dir = os.path.join(to_path,rel)
                local_path = os.path.join(local_dir,file)
                os.makedirs(local_dir, exist_ok=True)
                Path(local_path).symlink_to(opath) 
                #Docs Said was reversed? Test
            
            if keep_empty_folders:
                #Bit of a stupid way to go about it keeping 
                for opath, root, rel, file in self._walk(from_path, yield_files=False, yield_dirs=True):
                    local_dir = os.path.join(to_path,rel)
                    local_path = os.path.join(local_dir,file)
                    os.makedirs(local_dir, exist_ok=True)
                    
        else:
            Path(to_path).symlink_to(from_path) 
            #Docs Said was reversed? Test


    def copy(self, from_path, to_path):
        if Path(from_path).is_dir():
            shutil.copytree(from_path, to_path, symlinks=False)
        else:
            shutil.copy2(from_path, to_path, follow_symlinks=True)

    def inlink(self, *paths, root_from=None, root_to='.'):
        ''' Link input paths (dir or fp). Keeps empty folders'''
        for from_path, to_path in self.find_relative_cmds(*paths, root_from=root_from, root_to=root_to):
            self.link(from_path, to_path)

    def incopy(self, *paths, root_from=None, root_to='.'):
        ''' Copy input paths (dir or fp). Keeps empty folders'''
        for from_path, to_path in self.find_relative_cmds(*paths, root_from=root_from, root_to=root_to):
            self.copy(from_path, to_path)

    def find_relative_cmds(*paths, root_from=None, root_to='.'):
        '''
        :paths: argument paths, can be from anywhere
        :root_from: Root to truncate paths's root. If None, it is assumed that the `root_from = os.path.split[-2]`. Error pre-link if every item doesn't have `root_from` Must be Absolute path.
        :root_to: relative target dir inside of self.dp (cwd)
        '''
        local_root = Path(root_to).relative_to(self.dp)
        cmds = []
        for from_path in paths:
            if root_from:
                relative_path = Path(from_path).relative_to(root_from)
                assert not relative_path.startswith('..')
            else:
                relative_path = os.path.split()[-1]
            
            local_path = Path(os.path.join(local_root,relative_path)).resolve()
            cmds.append(from_path, local_path)
        return cmds
