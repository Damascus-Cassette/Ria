''' Job Database Model '''

from sqlalchemy     import (Column              ,
                            Boolean             ,
                            ForeignKey          ,
                            Integer             ,
                            List                ,
                            String              ,
                            create_engine       ,
                            Table               ,
                            Enum as db_Enum     ,
                            Engine as EngineType,
                            )

from sqlalchemy.orm import (declarative_base    , 
                            relationship        , 
                            sessionmaker        , 
                            Mapped              , 
                            mapped_column       ,
                            Session as SessionType
                            )
from enum import Enum

Base = declarative_base()

class Space_Types(Enum):
    IMPORT = 'IMPORT'
    EXPORT = 'EXPORT'
    VIEW   = 'VIEW'

class Job_States(Enum):
    EDITABLE   = 'EDITABLE'     #The only stage when something should be editing an actual job, otherwise the DB should be forked and put into this state.
    READY      = 'READY'
    PROCESSING = 'PROCESSING'
    PAUSED     = 'PAUSED'
    WAITING    = 'WAITING'      #Special waiting for 
    CANCELED   = 'CANCELED'
    COMPLETE   = 'COMPLETE'

class Task_Types(Enum):
    GRAPH_EXECUTE = 'GRAPH_EXECUTE'
    PING          = 'PING'
    CMD           = 'CMD'

class POI_Types(Enum):
    TASK             = 'TASK'
    INPUT            = 'INPUT'
    OUTPUT           = 'OUTPUT'
    CHECKPOINT       = 'CHECKPOINT'
    BREAKPOINT       = 'BREAKPOINT'
    VIS_META_GENERIC = 'VIS_META_GENERIC'
    VIS_EXEC_GENERIC = 'VIS_EXEC_GENERIC'


class DB_Job_Info(Base):
    ''' Metadata Container for this Graph, should only be one'''
    __tablename__ = 'job_info'
    source_graph = Column(String,primary_key=True)
    session_id   = Column(String)
    label        = Column(String)
    author       = Column(String)
    user         = Column(String)
    state        = Column(db_Enum(Job_States))


class DB_Spaces(Base):
    ''' Container for ascocated spaces, should contain method of affecting primary file db'''
    __tablename__ = 'ascociated_spaces'
    
    space_key    = Column(String, primary_key=True)
    space_type   = Column(db_Enum(Space_Types))
    users: Mapped[List["DB_Point_Of_Interest"]] = relationship(back_populates="cache")


class DB_Memo(Base):
    ''' Container for asc-memo spaces, (Partial-override-caches) '''
    # Will have to be adjusted when I figure out the details of Memo in meta vs exec
    __tablename__ = 'ascociated_memos'
 
    space_key    = Column(String, primary_key=True)
    space_type   = Column(db_Enum(Space_Types))
    users: Mapped[List["DB_Point_Of_Interest"]] = relationship(back_populates="memo")


class DB_Point_Of_Interest(Base):
    ''' Working rep of all points of interest on a Graph, Used for Visual Interface '''
    __tablename__ = 'points_of_interest'

    id           = Column(Integer, autoincrement=True)
    
    exec_node_id = Column(String, primary_key=True)
    meta_node_id = Column(String, primary_key=True, nullable=True)

    type = Column(db_Enum(POI_Types))
    
    task_data      : Mapped["DB_Task"] = relationship(back_populates="poi", default=None)
    
    cache_id       : Mapped[str] = mapped_column(ForeignKey("ascociated_spaces.space_key" ), nullable=True)  
    cache          : Mapped['DB_Spaces'] = relationship(back_populates = 'users')

    memo_id        : Mapped[str] = mapped_column(ForeignKey("ascociated_memos.space_key"  ), nullable=True)  
    memo           : Mapped['DB_Memo']   = relationship(back_populates = 'users')

    vis_parent_id  : Mapped[str] = mapped_column(ForeignKey("vis_zones.id"                ),nullable=True)
    vis_parent     : Mapped['DB_Zone']   = relationship(back_populates = 'children')

    vis_zone_start = Column(Boolean, default=False)
    vis_zone_end   = Column(Boolean, default=False)

    vis_links_left  :Mapped[List["Visual_Links"]]     = relationship(secondary='DB_Point_Of_Interest', back_populates='left' )
    vis_links_right :Mapped[List["Visual_Links"]]     = relationship(secondary='DB_Point_Of_Interest', back_populates='right')
        #Prettty sure this is how it works


class DB_Task():
    ''' 1 to 1 relationship with a POI object (Not required to have a POI object, but spawned with when it's processing a graph) '''
    __tablename__ = 'tasks'

    id              = Column(String,primary_key=True)
    task_label      = Column(String,) 
    task_state      = Column(db_Enum(Job_States))
    task_type       = Column(db_Enum(Task_Types))

    depends_on_me   : Mapped[List["DB_Task"]] = relationship(secondary='DB_Task', back_populates='right')
    depends_on      : Mapped[List["DB_Task"]] = relationship(secondary='DB_Task', back_populates='left' )
    
    poi_id          : Mapped[int]                    = mapped_column(ForeignKey("points_of_interest.id"), nullable=True)
    poi             : Mapped['DB_Point_Of_Interest'] = relationship(back_populates='task_data')

    pickups         : Mapped['DB_task_pickups']      = relationship(back_populates='task_data')
    # banned_


class Dependency_Links():
    __tablename__ = 'dependency_links'
    left  : Mapped[str] = mapped_column(ForeignKey("DB_Task.id"),nullable=True, primary_key=True)
    right : Mapped[str] = mapped_column(ForeignKey("DB_Task.id"),nullable=True, primary_key=True)


class DB_task_pickups():
    ''' Each pickup of a task streams here '''
    __tablename__ = 'task_pickups'
    
    id = Column(Integer, autoincrement = True, primary_key = True)
    task_data    : Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    
    worker_id      = Column(String)
    log_location   = Column(String) #Refering to a stream
    event_location = Column(String) #Refering to filtered events / communication between the two.
        #Location on the manager's side.


class DB_Zone(Base):
    ''' Visual container class spawned by zones. (label,inst_id,meta_id) should be passed back by the zones in backwards context '''
    id          = Column(Integer, autoincrement=True)
    label       = Column(String)
    meta_id     = Column(String , primary_key =True)
    inst_id     = Column(String , primary_key =True)
    
    vis_parent_id  : Mapped['DB_Zone']  = mapped_column(ForeignKey("vis_zones.id"), nullable=True)

    poi_users      : Mapped[List["DB_Point_Of_Interest"]] = relationship(back_populates="vis_parent")
    zone_users     : Mapped[List["DB_Zone"]]              = relationship(back_populates="vis_parent")


class Visual_Links():
    __tablename__ = 'dependency_links'
    left  : Mapped[int] = mapped_column(ForeignKey("DB_Point_Of_Interest.id"),nullable=True, primary_key=True)
    right : Mapped[int] = mapped_column(ForeignKey("DB_Point_Of_Interest.id"),nullable=True, primary_key=True)