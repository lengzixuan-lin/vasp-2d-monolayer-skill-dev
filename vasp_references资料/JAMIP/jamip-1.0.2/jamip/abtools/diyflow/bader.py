import os
import numpy as np
from .miniflow import MiniFlow

class Bader(MiniFlow):
 
    yaml = {'nedos': 3001,
            'laechg': True,
            'lcharg': True,
            'lwave': False,
            'nsw': 0 
           }

    def __init__(self,func,stdin=None,rootdir=None,*args,**kwargs):
        MiniFlow.__init__(self,func,stdin,rootdir)
        stdout = os.path.join(self.rootdir,'electric','bader')
        self.diy_calculator(func,stdout=stdout,stdin=stdin)

    def diy_calculator(self,func,stdout,stdin=None):
        from os.path import join, exists
        from jamip.abtools.vasp.check import CheckStatus

        check = CheckStatus(self.rootdir)

        if not exists(stdout):
            os.makedirs(stdout)

        # scf %
        self.scf_calculation(func,stdout,stdin)

        # bader %
        self.bader_calculation(stdout)

        # update task status %
        status = check.success(join(stdout,'OUTCAR'),'bader')
        if self.check(self.rootdir):
            func.tasks.diy.bader.finish = True
        else:
            status['success'] = False
        check.write_status(status, stdout)

    def scf_calculation(self,vasp,stdout,stdin=None):
        from copy import deepcopy

        # loop the kpoints % 
        self.calculator(vasp, stdout, stdin, incar=vasp.tasks.diy.bader)

    def bader_calculation(self,stdout):
        from os.path import exists,join
        from jamip.analysis.vasp.chgcar import GrepChgcar

        # check files %
        if not exists(join(stdout,'AECCAR2')) or not exists(join(stdout,'AECCAR0')):
         
            print('AECCAR not exists! bader calculation stop.')
            return False

        GrepChgcar().chgcar_sum(path=stdout)
        os.chdir(stdout)
        os.popen("bader CHGCAR -ref CHGCAR_sum > bader.log").readline()
        os.chdir(self.rootdir)

    @classmethod
    def check(self,path):
        from os.path import join,exists,basename,getsize
        if basename(path) != 'bader':
            file = join(path,'electric','bader','ACF.dat')
        else:
            file = join(path,'ACF.dat')
        if exists(file) and getsize(file):
            print('Bader calculation finish.')
            return True
        else:
            return False

    @classmethod
    def create(self,params):
        '''
        isym : -1, complete k_points
        laechg: create AECCAR0, AECCAR1, AECCAR2
        lcharg: save chgcar
        '''
        from jamip.abtools.base.tasks import Incar

        data = Incar('bader',self.yaml)
        data.update(params)

        return data
