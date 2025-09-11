''' Startup the entities from this file. TODO: Move to a better location. '''

from fastapi import FastAPI
from .Entity_Declaration import Worker_Local

worker = Worker_Local()
app     = worker.attach_to_app(FastAPI())