import os
from .vaspflow import VaspFlow

class CorrectingFlow(VaspFlow):

    def __init__(self,root):
        from jamip.compute.cluster import Cluster
        from os.path import dirname,abspath
        self.rootdir = abspath(root)
        self.cluster = Cluster(dirname(dirname(self.rootdir))) 

    def debug(self, error, vasp, stdout, stdin=None, origin_incar={}, **kwargs):

        from .check import CheckStatus
        from .tasks import Incar
        from os.path import exists,join
        from copy import deepcopy
        import shutil
        import json

        # continue calcultions %
        check = CheckStatus(self.rootdir)
        self.origin_stdout = stdout
        vasp = deepcopy(vasp)

        # get_correct_params %
        incar = Incar('debug',self.analysis(error, stdin))
        incar.downdate(origin_incar)

        # makedirs %
        debug_root = join(self.rootdir,'debug')
        stdout = join(self.rootdir,'debug','tmp')
        if not exists(debug_root): os.makedirs(debug_root)
        if not exists(stdout): os.makedirs(stdout)

        stdout = self.calculator(vasp,stdout,stdin,incar,overwrite=True,debug=True)

        return stdout,incar

    def analysis(self, error, stdin):
        import re
        from os.path import join
        from jamip.analysis.vasp import Finder
        from ruamel import yaml
        from .monitor import Writelog 

        # get_tasktype %
        if stdin is not None:
            fd = Finder(stdin)

        # read_error_params from error.json %
        path = os.environ['HOME']+'/.jamip/env/error.yaml'
        with open(path,'r') as f: 
            errors = yaml.safe_load(f)
        params = errors[error][1]
        if params == None:
            raise SystemExit("Exit vasp calculation for Error %s" %error)

        # analysis_error_params %
        for key,value in params.items():
            if isinstance(value,int) or isinstance(value,float):
                pass
            elif isinstance(value,str) or isinstance(value,unicode):
                if value.lower() == 'true':
                    params[key] = True
                elif value.lower() == 'false':
                    params[key] = False
                elif '+' in value or '-' in value or '*' in value or '/' in value:
                    t = re.findall(r'[A-Za-z]+',value)
                    for tag in t:
                        value = value.replace(tag,str(jg.grep(tag.lower())),1)
                    params[key] = eval(value)

        return params
