from .TestModule_V2    import main as TestModule_V2
from .Execution_V2     import main as Execution_V2 
# from .Monadish_Interface_1_1     import main as Monadish_Interface_1_1 
from .Monadish_Interface_1_2     import main as Monadish_Interface_1_2 
from .Operations_V1 import main as Operations_V1

modules = [
           TestModule_V2,
           Execution_V2,
           Monadish_Interface_1_2,
           Operations_V1,
           ]
    #All module versions allowed to load

base_module_defaults = {
    TestModule_V2.UID : TestModule_V2.Version,
    Execution_V2.UID  : Execution_V2.Version ,
    Operations_V1.UID : Operations_V1.Version,
    }
    #Default versions produced