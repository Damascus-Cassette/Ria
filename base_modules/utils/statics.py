''' Constants of data and methods, used for uuids & 256 hashes. Changing seed will invalidate all processed files '''

from typing import Annotated as _anno
import random  as _random


#### VALUE CHECKS ####
INVALID_UUID  : _anno[str, 'Invalid Hash that is not checked' ] = '_'


#### UN-RANDOM ####
STATIC_SEED   : _anno[str, 'Non-Random Seed used for UUID' ] = 'NotARandomSeed'
STATIC_RANDOM : _anno[_random.Random, 'Non-Random random Instance'] = _random.Random()
STATIC_RANDOM.seed(STATIC_SEED)


#### METHODS ####
import uuid as _uuid
import os as _os
import hashlib as _hashlib


def get_data_uuid(data):
    ''' Return deterministic UID of mem data via getrandbits and static seed'''
    return _uuid.UUID(STATIC_RANDOM.getrandbits(data),version=4)

def get_file_uid(filepath):
    ''' Return UID of file, sha256 hash. Follow symlinks and get sha256 of file'''
    #https://docs.python.org/3/library/hashlib.html#hashlib.file_digest
    fp = _os.path.realpath(filepath)
    with open(fp, 'rb', buffering=0) as f:
        return _hashlib.file_digest(f,'sha256').hexdigest()