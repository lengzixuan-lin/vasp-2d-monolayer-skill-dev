import os
import numpy as np
from .miniflow import MiniFlow

class Poisson(MiniFlow):

    yaml = {'scale':'0.98 0.99 1.00 1.01 1.02',
            'axis' :'x y z',
            'parallel': 4
           }

    def __init__(self,func,stdin=None,rootdir=None,*args,**kwargs):

        MiniFlow.__init__(self,func,stdin,rootdir)
        stdout = os.path.join(self.rootdir, 'mechanic', 'poisson')
        self.diy_calculator(func,stdout=stdout,stdin=stdin)
	
    def diy_calculator(self, func, stdout, stdin=None):
        from os.path import join, exists

        if not exists(stdout):
            os.makedirs(stdout)

        # subtasks %
        self.poisson_calculation(func, stdout, stdin)
        func.tasks.diy.poisson.finish = True

    def poisson_calculation(self, vasp, stdout, stdin):
        from copy import deepcopy
        from os.path import join

        params = vasp.tasks.diy.poisson
        # append relax params %
        if vasp.tasks.relax != None and len(vasp.tasks.relax):
            params.downdate(vasp.tasks.relax)
        else:
            relax = {'isif': 3, 'ibrion':2, 'nsw':100}
            params.downdate(relax)

        structure = self.load_structure(vasp, stdin)
        axis = ['x','y','z']
        subtasks = []
        
        for i in params.axis:
            if len(params.axis) == 3: 
                optcell = np.array([1,1,1])
                optcell[i] = 0
            if len(params.axis) == 2:
                optcell = np.array([0,0,0])
                optcell[params.axis] = 1
                optcell[i] = 0
            vasp.optcell = optcell

            for scale in params.scale:
                if abs(scale -1) < 1e-4: continue
                # resize lattice %
                cell = deepcopy(structure)
                lattice = cell.lattice
                lattice[i] = lattice[i]*scale 
                cell.lattice = lattice
                cell.comment_line = 'POISSON-%s-%s' %(axis[i],scale)
                # calaulation %
                subout = join(stdout,'%s-%s' %(axis[i],scale))
                incar = vasp.set_input(cell, subout, True, params)
                subtasks.append(subout)

        program = self.get_program(vasp, incar)
        parallel = min(len(subtasks),params.parallel)
        self.subtask_calculation(vasp, subtasks, 'poisson', program, parallel)

        return True

    @classmethod
    def check(self,path):
        from os.path import join,exists,basename,getsize
        from jamip.abtools.vasp.check import CheckStatus
        status = CheckStatus.load_status(path)
        if 'poisson' in status and status['poisson'].finish:
            return True
        return False

    @classmethod
    def create(self,params):
        '''
        load the poisson parameter save with diyinput     

        self.scale = '0.98 0.99 1.00 1.01 1.02'
        self.axis = 'x y z'
        '''
        from jamip.abtools.base.tasks import Incar
        import numpy as np

        axis = {'x':0, 'y':1, 'z':2}
        data = Incar('poisson')
        try:
            data.scale = np.array(params.pop('scale').split(), dtype=float)
            data.axis = np.array([axis[i] for i in params.pop('axis').split()])
        except:
            raise KeyError("Missing necessary params for poisson! task exit")
        if 'parallel' in params:
            data.parallel = params.pop('parallel')
        else:
            data.parallel = 1
        data.update(params)

        return data
 

