from fastapi  import FastAPI, HTTPException, APIRouter, UploadFile
from pydantic import BaseModel

from ..settings_base import settings_base

from .fast_api_base import net_io, api
from ..db_interface import db_interface
app = FastAPI()

class itenerary(BaseModel):
    ...

class Manager(net_io):
    def __init__(self, settings:settings_base,db:db_interface):
        
        self.router = APIRouter()
        api.construct(self,self.router)
        self.app = FastAPI()
        self.db  = db
    
    def start(self):
        ''' Start manager with settings '''


    # @api.get('/echo_test')
    # def echo_connection(self):
    #     return {
    #         'FROM_INST' : self.name,
    #         'CALLED'    : self.api.who_am_i(self.connection)
    #         }

    @api.put('/spaces/store')
    def space_store(self,space_id,iten:itenerary):
        ''' Creates space using Iten '''
        self.db.repo_Space.store()

    @api.get('/space/{space_id}/i')
    def space_info(self,space_id):
        ''' Generic 1st level info of space (mySpaces, myFiles, inX) '''

    @api.get('/space/{space_id}/d')
    @api.get('/space/{space_id}/iten/data')
    def space_iten_base(self,space_id,)->itenerary:
        ''' Iten of space and all children '''

    @api.get('/space/{space_id}/iten/diff')
    def space_iten_dif(self,space_id,iten:itenerary)->itenerary:
        ''' Dif iten submitted and return files & spaces not on this server '''


    @api.put('/files/store')
    def file_store(self,file_id, upload:UploadFile):
        ''' Upload file to this server, validate upload '''
    @api.get('/file/{file_id}/i/')
    def file_info(self,file_id):
        ''' Info on file ID, including names and spaces '''
    @api.get('/file/{file_id}/d/')
    def file_data(self,file_id):
        ''' File address for downloading. Error if gone or placeholder if decayed '''


    @api.post("/users/io")
    def user_manage(self,user_id:str,data):
        ''' Intakes user definition to change user in db '''
    @api.get("/user/{user}/i/")
    def user_info(self,):
        ''' Info about user, including sessions & exports'''

    @api.post("/subusers/io")
    def subuser_manage(self,subuser_id:str,data):
        ''' Intakes subuser definition to change user in db '''        
    @api.get("/subuser/{subuser}/i")
    def subuser_info(self):
        ''' Info about subuser, including sessions & exports'''

    @api.post("sessions/io")
    def session_manage():
        ''' Manage session, including creating and changing state. Such as adding imports and exports '''
    @api.get("session/{session}/i")
    def session_info():
        ''' Info about session, such as User, Imports, Exports, ect '''

    @api.post("views/io")
    def view_manage():
        ''' Manage view, including creating and changing state '''
    @api.post("views/expose")
    def view_expose():
        ''' Expose View to folder in disc & return it '''
    @api.get("view/{view}/i")
    def view_info():
        ''' Info about view, such as User, views, views, ect '''
    @api.get("view/{view}/iten")
    def view_iten():
        ''' '''

    @api.post("imports/io")
    def import_manage():
        ''' Manage import, including creating and changing state '''
    @api.post("imports/expose")
    def import_expose():
        ''' Expose import to folder in disc & return it '''
    @api.get("import/{import}/i")
    def import_info():
        ''' Info about import, such as User, Imports, Exports, ect '''
    @api.get("import/{import}/iten")
    def import_iten():
        ''' '''

    @api.post("exports/io")
    def export_manage():
        ''' Manage export, including creating and changing state '''
    @api.post("exports/expose")
    def export_expose():
        ''' Expose export to folder in disc & return it '''
    @api.get("export/{export}/i")
    def export_info():
        ''' Info about export, such as User, exports, Exports, ect '''
    @api.get("export/{export}/iten")
    def export_iten():
        ''' '''
