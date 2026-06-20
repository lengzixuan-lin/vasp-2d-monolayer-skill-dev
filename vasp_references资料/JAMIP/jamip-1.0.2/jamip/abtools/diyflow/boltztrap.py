import os
import numpy as np
from .miniflow import MiniFlow

class Boltztrap(MiniFlow):
 
    yaml = {'kspacing': 0.05}

    def __init__(self,func,stdin=None,rootdir=None,*args,**kwargs):
        MiniFlow.__init__(self,func,stdin,rootdir)
        stdout = os.path.join(self.rootdir,'electric','boltztrap')
        self.diy_calculator(func,stdout=stdout,stdin=stdin)

    def diy_calculator(self,func,stdout,stdin=None):
        from os.path import join, exists, getsize
        from jamip.abtools.vasp.check import CheckStatus

        if not exists(stdout):
            os.makedirs(stdout)

        check = CheckStatus(self.rootdir)

        # finish_flag %
        output = join(stdout,'boltztrap.dat')
        if exists(output):
            if getsize(output):
                print('BoltzTrap calculation finish.\n')
                return
            else:
                os.remove(output)

        # high-mesh scf %
        self.scf_calculation(func,stdout,stdin)

        status = check.success(join(stdout,'OUTCAR'),'boltztrap')
        if status['success'] != True:
            print('Boltztrap calculation stop.')
        # boltztrap %
        self.boltz_calculation(stdout)

        # update task status %
        if self.check(self.rootdir):
            check.write_status(status, stdout) 
            func.tasks.diy.boltztrap.finish = True

    def scf_calculation(self,vasp,stdout,stdin=None):
        from os.path import join, exists, dirname
        from ..vasp.check import CheckStatus
        from jamip.abtools.vasp.vaspio import VaspIO
        from copy import deepcopy

        # loop the kpoints % 
        params = vasp.tasks.diy.boltztrap
        scfvasp = deepcopy(vasp)
        scfvasp.kpoints = params['kspacing'] if 'kspacing' in params else 0.05
        self.calculator(scfvasp, stdout, stdin, incar=params)
        # write symmerty % 
        VaspIO.write_symmetry(vasp.structure.bandStructure(),stdout)

    def boltz_calculation(self,stdout):
        from os.path import exists,join
        import shutil

        src = os.environ['HOME']+'/.jamip/bin'
        for f in ['massall.x','ani_Boltz_vasp','BoltzTrap_vasp.def']:
            if exists(join(stdout,f)): 
                continue
            os.symlink(join(src,f), join(stdout,f))

        # run program % 
        os.chdir(stdout)
        os.popen('./massall.x > boltztrap.dat').readline()
        os.chdir(self.rootdir)
         
    @classmethod
    def create(self,params):
        '''
        boltztrap calculation 
        '''
        from jamip.abtools.base.tasks import Incar
        data = Incar('boltztrap',params)
        return data

    @classmethod
    def check(self,path):
        from os.path import join,exists,getsize,basename
        if basename(path) != 'boltztrap':
            file = join(path,'electric','boltztrap','mass.dat')
        else:
            file = join(path,'madd.dat')
        if exists(file) and getsize(file):
            print('Boltztrap calculation finish.')
            return True
        else:
            return False
