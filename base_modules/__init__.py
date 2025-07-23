from .TestModule_V1 import main as TestModule_V1

modules = [TestModule_V1]
    #All module versions allowed to load
base_module_defaults = {
    TestModule_V1.UID:TestModule_V1.Version
    }
    #Default versions produced