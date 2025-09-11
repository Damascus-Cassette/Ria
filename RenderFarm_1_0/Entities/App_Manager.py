''' Startup the entities from this file. TODO: Move to a better location. '''

from fastapi import FastAPI
from .Entity_Declaration import Manager_Local

manager = Manager_Local()
app     = manager.attach_to_app(FastAPI())