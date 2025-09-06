''' Isolated database model per task '''

class db_Job_Info():
    'Singleton Info'
    source_graph : str
    label        : str
    author       : str
    user         : str

class db_spaces(DB_Base):
    type     : Enum #Import, Export, View
    use_type : Enum #Graph(Singleton),User_Data,Cache,Memo
    key      : str
    #And funcs to access as it relates to the job

class db_cache_asc(DB_Base):
    ''' Local cache asc, additive to global in process but stored seperate'''
    state_key      : str
    db_spaces_key : str

class db_memo(DB_Base):
    ''' References to memo-cache spaces. (partial-override-caches?) via exec/meta node ID. Must be exposed on primary graph. '''
    is_meta       : bool

    instance_key  : str
    db_spaces_key : str
    
class db_dep_links(DB_Base):
    ''' Dependency links between POI[Tasks] for execution order. '''
    left_task  : str
    right_task : str


from enum import Enum
class Task_State(Enum):
    ...
    # DISCOVERED = ''
    # DISCOVERED = ''

class POI_Type(Enum):
    TASK             = 'TASK'
    VIS_META_INPUT   = 'VIS_META_INPUT'
    VIS_META_GENERIC = 'VIS_META_GENERIC'
    VIS_EXEC_GENERIC = 'VIS_EXEC_GENERIC'

class db_poi():
    ''' Points of interest, visual and task '''
    type  : POI_Type #Task or Vis_Only
    state : Task_State
    
    cache : str #reference to cache in file db
    
    label           : str

    is_meta         : bool
    is_input        : bool
        #may want to abstrac these two?

    exec_node_id    : str
    meta_node_id    : str
    zone_parent     : str = None

    deps : list[Self]

    task_tags : list[str]


class db_vis_links(DB_Base):
    ''' Visual relationship links between POI '''
    
class db_vis_zone(DB_Base):
    ''' Visual zone, discovered/noted in compile via backwards dep notation'''
    label   : str
    meta_id : str
    inst_id : str
    parent  : str # refering to another vis zone