from contextvars import ContextVar
import os

CURRENT_DIR = ContextVar('CURRENTDIR', default = os.getcwd())
# raise Exception(CURRENT_DIR.get())