import hashlib
import random
import uuid
import os

from __future__ import annotations
from typing     import Self
from os         import path as osp


class _utils:
  r = random('Random_Key')
  
  @classmethod
  def get_uid_stable(cls,value)->str:
    return uuid.UUID(value,random = cls.r)
      

class fm_file:
  ''' Acts as a structured dict '''
  __slots__ = ['sha256','name']
  uuid   : str
  name     : str

  def __init__(self,fp):
    if osp.is_symlink(fp):
      fp = osp.realpath(fp)

    with open(fp,'rb') as f:
      self.uuid = hashlib.file_digest(f,'sha256').hexdigest()

class fm_space:
  ''' Acts as a structured dict '''
  __slots__ = ['uuid','spaces','files']
  uuid : str
  name   : str
  spaces : list[fm_space]
  files  : list[fm_file]

  def __init__(self, dp):
    self.files  = []
    self.spaces = []

    for item in os.listdir(dp):
      self.name = osp.split(dp)[1]
      
      if osp.isfile(item):
        self.files.append(fm_file(item))
      
      else:
        self.spaces.append(self.__class__(dp))

      self.sort()
      self.sumhash()
    
  def sort(self):
    self.spaces = sorted(self.spaces,lambda i: i.name)
    self.files  = sorted(self.files, lambda i: i.name)

  def sumhash(self):
    res = ''

    for item in self.spaces:
      res.append(item.uuid)
    for item in self.files:
      res.append(item.uuid)

    self.uuid = _utils.get_uid_stable(res)

    return self.uuid
  
  def yield_spaces(self,recur=True,incl_self=True):
    ''' Yield spaces recursivly, deepest should be returned first '''
    for space in self.spaces:
      if recur:
        for e in [x for x in space.yield_spaces(recur=True,incl_self=False)]:
          yield e
      yield space

    if incl_self:
      yield self

  def yield_items(self,recur=True):
    ''' Yield file items recursivly, deepest should be returned first '''
    for space in self.spaces:
      if recur:
        for f in [x for x in space.yield_items(recur=True)]:
          yield f

    for f in self.files:
      return f

  
class file_manager_io():
  root : str 

  def __init__(self,
          storage_loc, 
          space_attrs:list[str]=[], 
          file_attrs :list[str]=[],
          ):
    self.root = storage_loc
    self.create_db(space_attrs=space_attrs,file_attrs=file_attrs)
  
  def path_hash(self,path):
    ''' get via sha256 of all files's origins *and* subspaces junctions hashes (their folder name)'''
    
  def get_sha256(self,path):
    assert osp.exists(path)
    if osp.isdir(path):
      assert self.files_are_uploaded()
      assert self.folders_are_uploaded()
      return 's_'+self.dir_hash(path)
    else:
      return 'f_'+hashlib(path)

  def store_file (self,fp):
    ''' Stores a file, replaces the original with a symlink. Returns UID ''' 
  def store_space(self,dp):
    ''' Stores a folder as a space, stores all files first. Replaces with junction. Returns UID '''
  
  def pull_space(self,uid,res_dir,name):
    ''' Place junction of folder as res_dir/name/ '''
  def pull_file(self,uid,res_dir,name):
    ''' Place symlink of file in dir/name.ext '''

  def fetch_space_by_attr(self,**kwargs):
    ''' Find's space Entries by attr:key filters '''
  def fetch_file_by_attr(self,**kwargs):
    ''' Find's file Entries by attr:key filters '''
    
  def remove_space(self, uid):
    ''' Removes space from being tracked. Files referencing space lose that tracked User '''
  def remove_file(self,uid):
    ''' Removes a .blob from the database. Returns a confirmation cmd if their are tracked users '''

  def cleanup_space(self, uid):
    ''' port of remove_space '''
  def cleanup_file(self):
    ''' Removes files with 0 Users or other rules '''
  
  def deep_clean(self):
    ''' Removes all tracked 0 user spaces, files recursivly '''
  def criteria_clean():
    ''' Removes all spaces with given criteria '''

  def info(self,uids):
    #return info about UIDs
    ...

  def localize_folder():
    ''' Take symlinks and pull them into local copies. Used in export functionality '''


class file_manager_net_manager:
  ''' handles the exposure/io of the manager on the network '''
  ''' Component of flask/constructs flask, responding to net_client commands'''
  def __init__(file_manager_io_inst, port):
    ...


class file_manager_net_client:
  ''' Connection to ext manager instance, can handle rudimentary tasks '''
  ''' Curl commands to known manager address '''
  def __init__(file_manager_io_inst, manager_addr):
    ...
