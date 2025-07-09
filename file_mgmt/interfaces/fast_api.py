from fastapi  import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel

from .fast_api_base import net_io, api

app = FastAPI()

class Manager(net_io):
    def __init__(self, name: str, con):
        self.name = name
        self.router = APIRouter()
        self.connection = con
        api.construct(self,self.router)

    # @api.get('/echo_test')
    # def echo_connection(self):
    #     return {
    #         'FROM_INST' : self.name,
    #         'CALLED'    : self.api.who_am_i(self.connection)
    #         }

    @api.put('/file/store')
    def store_file():
        ...
    @api.get('/file/i/{file_id}')
    def get_file_info(file_id):
        ...

