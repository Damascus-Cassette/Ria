
from fastapi import FastAPI
from .Entity_Declaration import Client_Local

client = Client_Local()
app     = client.attach_to_app(FastAPI())