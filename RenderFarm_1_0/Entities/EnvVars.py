from contextlib import ContextVar
import os

CURRENT_DIR = ContextVar('CURRENTDIR', default = os.curdir)