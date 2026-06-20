import os
import numpy as np
from .miniflow import MiniFlow

class Jdos(MiniFlow):
 
    yaml = {'ismear': -5,
            'isymm': 1,
            'nedos': 3001,
            'ommin': 0,
            'ommax': 10,
            'lsearch': False
           }

    def __init__(self,func,stdin=None,rootdir=None,*args,**kwargs):
        MiniFlow.__init__(self,func,stdin,rootdir)
        stdout = os.path.join(self.rootdir,'optic','jdos')
        self.diy_calculator(func,stdout=stdout,stdin=stdin)

    def diy_calculator(self,func,stdout,stdin=None):
        from os.path import join, exists
        from jamip.abtools.vasp.check import CheckStatus

        check = CheckStatus(self.rootdir)

        if not exists(stdout):
            os.makedirs(stdout)

        # finish_flag %
        if self.check(self.rootdir):
            func.tasks.diy.jdos.finish = True
            return

        # optics check %
        optics = None
        if func.tasks.optic != None and 'optics' in func.tasks.optic:
            if func.tasks.optic.optics.finish:
                optics = True
        if optics != True:
            print('JDOS calcuiation need optics result!')
            return


        # jdos %
        self.jdos_calculation(func,stdout)

        # update task status %
        status = {'task':'jdos',
                  'finish': True,
                  'success': self.check(self.rootdir)
                 }
        check.write_status(status, stdout)
        func.tasks.diy.jdos.finish = True

    def jdos_calculation(self,vasp,stdout):
        from os.path import exists,join
        import shutil

        # create files %
        if not exists(stdout): os.makedirs(stdout)
        with open(join(stdout,'OPTCTR'),'w') as f:
            for key,value in vasp.tasks.diy.jdos.items():
                f.write('{0:12} = {1}\n'.format(key.upper(),value))

        # copy files %
        optics =join(self.rootdir,'optic','optics')
        shutil.copyfile(join(optics,'CONTCAR'),join(stdout,'POSCAR'))
        shutil.copyfile(join(optics,'IBZKPT'),join(stdout,'KPOINTS'))
        shutil.copyfile(join(optics,'OPTIC'),join(stdout,'OPTIC'))

        # run program %
        os.chdir(stdout)
        if vasp.tasks.diy.jdos['lsearch']:
            os.popen("optics > MATRIX").readline()
        else:
            os.popen("optics").readline()
        os.chdir(self.rootdir)

    @classmethod
    def check(self,root):
        from os.path import join,exists,getsize
        file = join(root,'optic','jdos','JDOS')
        if exists(file) and getsize(file):
            print('JDOS calculation finish.')
            return True
        else:
            return False

    @classmethod
    def create(self,params):
        '''
        '''

        from jamip.abtools.base.tasks import Incar
 
        yaml = {'ismear': -5,
                'isymm': 1,
                'nedos': 3001,
                'ommin': 0,
                'ommax': 10,
                'sigma': 0.1,
                'ltet': True,
                'ljdos': True,
                'ldos': False,
                'lkramers': True,
                'lexternal': False,
                'lsearch': False,
                'eminsearch': 0,
                'emaxsearch': 4,
                'ampmin': 0,
                'gamma': 0.0002
               }


        # jdos params %
        data = Incar('jdos', yaml)
        data.update(params)
        if data['ismear'] != -5:
            data['ltet'] = False

        return data

