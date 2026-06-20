from .check import __CheckStatus
from .parse import __ParseProcess
from .create import __CreateInput
from .output import __OutputData
from .vasptools import __Vasptools
from .softmanage import __Mysql,__Django
from jamip.compute import __LaunchTasks

def get_package_path():
    from os.path import abspath,dirname 
    return dirname(dirname(abspath(__file__)))

def runjamip():

    jamip = __ParseProcess()
    parse = jamip.__collect_parses__()
   
    if len(parse) ==0:
        print('jp -h/--help')
        print(get_package_path())
        return

    print(parse)
    if 'version' in parse:
        print(' V1.0 ')
 
    if 'run' in parse:
         __LaunchTasks(parse)   # launch unfinish task %  	

    if 'vasp_tools' in parse:
        __Vasptools().run(parse)	

    if 'output' in parse:
        __OutputData().run(parse)

    if 'db' in parse:
        from jamip.db.connect import __DBShell
        __DBShell(parse)

    if 'tarfile' in parse:
        __CompressData(parse)
	
    if 'check' in parse:
        __CheckStatus(parse)

    if 'input' in parse:
        __CreateInput(parse)

    if 'mysql' in parse:
        __Mysql(parse)

    if 'django' in parse:
        __Django(parse)
