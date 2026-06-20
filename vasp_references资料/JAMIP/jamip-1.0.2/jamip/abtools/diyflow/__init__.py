from os.path import dirname,realpath,abspath
from os import listdir
import importlib

def get_diy_modules():
    modules = []
    for module in listdir(get_diy_path()):
        if module.endswith('.py'):
            modules.append(module.split('.')[0])
    return modules

def get_diy_path():
    return abspath(dirname(realpath(__file__)))

def import_diy_module(module_name):
    if module_name not in get_diy_modules():
        if '_conv' in module_name:
            diy_module = importlib.import_module('jamip.abtools.diyflow.converge')
            diy_class = getattr(diy_module,module_name.capitalize())
        else:
            raise ImportError("Moudle not exists")
    else:
        diy_module = importlib.import_module('jamip.abtools.diyflow.'+module_name)
        diy_class = getattr(diy_module,module_name.capitalize())

    return diy_class
