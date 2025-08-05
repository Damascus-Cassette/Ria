from .TestModule_V1    import main as TestModule_V1
from .TestModule_V2    import main as TestModule_V2
# from ._Execution_V1    import main as Execution_V1 
from .Execution_V2     import main as Execution_V2 
# from .Execution_V2_1   import main 

modules = [TestModule_V1,
           TestModule_V2,
        #    Execution_V1,
           Execution_V2,]
    #All module versions allowed to load
base_module_defaults = {
    TestModule_V2.UID : TestModule_V2.Version,
    Execution_V2.UID  : Execution_V2.Version,
    }
    #Default versions produced