#TODO: A A file structure utility that generates folders, uploads them and verifys them

from ..db_struct import File,Space,asc_Space_NamedFile,_asc_Space_NamedSpace
from __future__ import annotations

class prepped_folder():
    ''' Representation of a possible or placed folder on disk and relationships'''
    name:str
    children: list[prepped_folder]
    parents : list[prepped_folder]
    files   : list[prepped_file]
    ####
    loc_on_disk : str
    id_on_db    : strs

    def __init__(self,name):
        self.name = name

    def verify(self,sqla_session):
        namedFile = sqla_session.query(_asc_Space_NamedSpace).filter_by(cName=self.name).first()
        my_p_names   = [x.name for x in self.parents]
        pSpace_names = [y.inSpaces for y in [x for x in namedFile.inSpaces]]
        return all([
            namedFile.cFile.id == self.expected_id,
            all([x in my_p_names for x in pSpace_names]),
            ])
    
    def place_on_disk(path, junctions=False):
        
        ...

class prepped_file():
    ''' Representation of a possible or placed file on disk and relationships'''
    parents : prepped_folder
    name:str
    data:str
    ####
    loc_on_disk : str
    id_on_db    : str
    expected_id : str

    def __init__(self,name,file_contents):
        self.name = name
        self.data = file_contents

    def verify(self,sqla_session):
        namedFile = sqla_session.query(asc_Space_NamedFile).filter_by(cName=self.name).first()
        my_p_names   = [x.name for x in self.parents]
        pSpace_names = [y.inSpaces for y in [x for x in namedFile.inSpaces]]
        return all([
            namedFile.cFile.id == self.expected_id,
            all([x in my_p_names for x in pSpace_names]),
            ])

class Test_Root():
    namespace : dict[str, prepped_folder|prepped_file]
    def __init__(self, on_disk_name, unique_prefix):
        self.namespace = {}
        self.on_disk_name  = on_disk_name
        self.prefix = unique_prefix


    def __call__(self, path:str|list[prepped_folder], file:str=None, /, file_contents:str=None):
        return self.ensure_chain(path, file, file_contents=file_contents)


    def ensure_chain(self, path:str, file:str=None, /, file_contents:str=None)->list[prepped_folder,prepped_file]:
        chain = path.split('/')
        
        file_inst = None
        if isinstance(chain[-1],str):
            if '.' in chain[-1]:
                assert not file
                file = chain.pop[-1]
                file_inst = self.return_file_inst(file_name=file,file_contents=file_contents)
        elif isinstance(chain[-1],prepped_file):
            file_inst = chain.pop[-1]

        chain = self.return_folder_chain(chain)

        if file_inst:
            chain.append(file_inst)

        return chain
            

    def return_folder_chain(self,chain:list[prepped_folder|str]):
        ret_chain   =  []
        last_folder = None
        for folder in chain:
            if isinstance(folder,str):
                _name = self.prefix + folder 
                if _name in self.namespace.keys():
                    folder_inst = self.namespace[_name]
                else:
                    folder_inst = prepped_folder(_name)
            else:
                folder_inst = folder

            if last_folder:
                last_folder.children.append(folder_inst)
                folder_inst.parents.append(last_folder)

            ret_chain.apppend(folder_inst)    

            last_folder = folder_inst

        return ret_chain

    def return_file_inst(self,file_name,file_contents)->prepped_file:
        _name = self.prefix + file_name
        if _name not in self.namespace.keys():
            file_inst = prepped_file(_name, file_contents)
            self.namespace[_name] = file_inst
        else:
            file_inst = self.namespace[_name]
        return file_inst
    

    def make_on_disk(symlink=False,Junction=False):
        ...

    def verify_folder_structure(symlink=False,Junction=False):
        ''' Post upload verify if symlinks and junctions are correct '''
        ...

    def verify_pattern(sqla_session):
        ...

    def verify_extract_folder_structure(localize=False):
        ''' Post extract to a location verify if symlinks and junction states are correct '''
        ...