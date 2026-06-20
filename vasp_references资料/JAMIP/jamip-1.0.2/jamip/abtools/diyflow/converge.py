import os
import numpy as np
from .miniflow import MiniFlow

class Cutoff_conv:

    yaml = {'encut':'300 450 30',
            'istart': 0,
            'icharg': 2,
            'parallel': 1,
           }

    @classmethod
    def create(self,params):
        '''
        load the poisson parameter save with diyinput     

        self.encut = '300 330 360 390 420 450' or
        self.encut = '300 450 30'
        '''
        from jamip.abtools.base.tasks import Incar
        import numpy as np

        data = Incar('cutoff-converge')
        try:
            cutoff = np.array(params.pop('encut').split(), dtype=float)
            if len(cutoff) == 3 and cutoff[2] < cutoff[1]:
                  start, end, step = cutoff
                  cutoff = np.arange(start, end, step)
                  cutoff = np.append(cutoff, end)
            data.cutoff = cutoff
        except:
            raise KeyError("Missing necessary params for poisson! task exit")
        if 'parallel' in params:
            data.parallel = params.pop('parallel')
        else:
            data.parallel = 1
        data.update(params)
        return data

class Kpoints_conv:

    yaml = {'kspacing':'0.1 0.3 0.05',
            'istart': 0,
            'icharg': 2,
            'parallel': 1,
           }

    @classmethod
    def create(self,params):
        '''
        load the poisson parameter save with diyinput     

        self.encut = '0.1 0.15 0.2 0.25 0.3' or
        self.encut = '300 450 30'
        '''
        from jamip.abtools.base.tasks import Incar
        import numpy as np

        data = Incar('kpoints-converge')
        try:
            kpoints = np.array(params.pop('kspacing').split(), dtype=float)
            if len(kpoints) == 3 and kpoints[2] < kpoints[1]:
                  start, end, step = kpoints
                  kpoints = np.arange(start, end, step)
                  kpoints = np.append(kpoints, end)
            data.kpoints = kpoints
        except:
            raise KeyError("Missing necessary params for poisson! task exit")
        if 'parallel' in params:
            data.parallel = params.pop('parallel')
        else:
            data.parallel = 1
        data.update(params)
        return data


class Converge(MiniFlow):


    def __init__(self,func, stdin=None,rootdir=None,*args,**kwargs):

        MiniFlow.__init__(self,func,stdin,rootdir)
        stdout = os.path.join(self.rootdir, 'relax')
        self.diy_calculator(func,stdout=stdout,stdin=stdin)
	
    def diy_calculator(self, func, stdout, stdin=None):
        from os.path import join, exists

        if not exists(stdout):
            os.makedirs(stdout)

        # subtasks %
        self.converge_calculation(func, stdout, stdin)
        func.tasks.converge.finish = True


    def converge_calculation(self, vasp, stdout, stdin=None, **kwargs):
        """
        function to relax the cell shape, internal inons and volume.
        """
        from os.path import join  
        from copy import deepcopy

        structure = self.load_structure(vasp, stdin)
        subtasks = []

        for task,params in vasp.tasks.converge.items():

            # create converge-test parameter % 
            if params.name == 'cutoff-converge':
                for cutoff in params.cutoff:
                    params['encut'] = cutoff
                    params.downdate(vasp.tasks.relax) 
                    # calaulation %
                    subout = join(stdout,'%s-%s' %('cutoff',np.round(cutoff)))
                    incar = vasp.set_input(structure, subout, True, params)
                    subtasks.append(subout)
         
            if params.name == 'kpoints-converge':
                for kspacing in params.kpoints:
                    params['kspacing'] = kspacing
                    params.downdate(vasp.tasks.relax) 
                    # calaulation %
                    subout = join(stdout,'%s-%s' %('kpoints',np.round(kspacing,3)))
                    incar = vasp.set_input(structure, subout, True, params)
                    subtasks.append(subout)

        program = self.get_program(vasp, incar)
        parallel = min(len(subtasks),params.parallel)
        self.subtask_calculation(vasp, subtasks, 'converge', program, parallel)
       
        return 

    @classmethod
    def check(self,path):
        from os.path import join,exists,basename,getsize
        from jamip.abtools.vasp.check import CheckStatus
        # status = CheckStatus.load_status(path)
        return True
 

