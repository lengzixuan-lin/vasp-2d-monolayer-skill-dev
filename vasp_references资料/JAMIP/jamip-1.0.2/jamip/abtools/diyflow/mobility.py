import os
import numpy as np
from .miniflow import MiniFlow

class Mobility(MiniFlow):
 
    yaml = {'scale': '0.98 0.99 1.00 1.01 1.02',
            'axis': 'x y z',
            'parallel': 4
           }

    def __init__(self,func,stdin=None,rootdir=None,*args,**kwargs):
        MiniFlow.__init__(self,func,stdin,rootdir)
        stdout = os.path.join(self.rootdir,'electric','mobility')
        self.diy_calculator(func,stdout=stdout,stdin=stdin)

    def diy_calculator(self,func,stdout,stdin=None):
        from os.path import join,exists
        from jamip.abtools.vasp.check import CheckStatus

        if not exists(stdout):
            os.makedirs(stdout)


        self.mobility_calculation(func, stdout, stdin)
        func.tasks.diy.mobility.finish = True

        print('mobility calculation finished')

    def mobility_calculation(self,vasp,stdout,stdin=None):
        from os.path import join, exists, dirname
        from ..vasp.check import CheckStatus
        from copy import deepcopy

        check = CheckStatus(self.rootdir)
        params = vasp.tasks.diy.mobility
        structure = self.load_structure(vasp, stdin)
        axis = ['x','y','z']

        # band calculation %
        if 'nbands' not in params:
            nbands = self.get_nband(vasp, stdin)
        edge = self.get_band_edge(vasp, stdin)
        if edge['gap'] > 0:
            bands = self.__set_emass_band(edge, params.axis)
        else:
            check.error_status(error='no-gap', path=stdout)
            return False

        # emass calculation %
        status = CheckStatus.load_status(self.rootdir)
        if 'emass' not in status or status['emass'].finish is False:
            self.electric_property(vasp, 'emass', stdin, join(self.rootdir,'electric','emass'))

        subtasks = []
        emassvasp = deepcopy(vasp)
        for i in params.axis:
            for scale in params.scale:
                if abs(scale -1) < 1e-4: continue
                cell = deepcopy(structure)
                lattice = cell.lattice
                lattice[i] = lattice[i]*scale
                cell.lattice = lattice
                cell.comment_line = 'Mobility-%s-%s' %(axis[i],scale)
                # scf calaulation %
                vasp.structure = cell
                stdscf = join(stdout,'%s-%s' %(axis[i],scale), 'scf')
                stdin = self.calculator(vasp, stdscf, stdin=None, incar=vasp.tasks.scf)
                # emass calculation %
                for dir,kpath in bands.items():
                    subout = join(stdout,'%s-%s' %(axis[i],scale), dir)
                    emassvasp.kpoints = kpath
                    incar = self.calculator_without_run(emassvasp, subout, stdin, incar=params)
                    subtasks.append(subout)

        program = self.get_program(vasp, incar)
        parallel = min(len(subtasks),params.parallel)
        self.subtask_calculation(vasp, subtasks, 'mobility', program, parallel)

        return True

    @classmethod
    def create(self,params):
        '''
        scale = '0.98 0.99 1.00 1.01 1.02'
        axis = 'x y z'
        band_insert = 50
        '''
        from jamip.abtools.base.tasks import Incar
 
        axis = {'x':0, 'y':1, 'z':2}
        data = Incar('mobility')

        # mobility necessary params %
        try:
            data.scale = np.array(params.pop('scale').split(),dtype=float)
            data.axis = np.array([axis[i] for i in params.pop('axis').split()])

        except:
            raise KeyError("Missing necessary params for mobility ! task exit")

        # mobility parameters %
        if 'parallel' in params:
            data.parallel = params.pop('parallel')
        else:
            data.parallel = 1

        data.update(params)
        return data

    def __set_emass_band(self, edge, axis):

        all = self.set_emass_band(edge)
        kpath = {}
        symbol = ['x', 'y', 'z']
        for i in axis:
            for key in all:
                if symbol[i] in key:
                    kpath[key] = all[key]

        return kpath

    def calculator_without_run(self, vasp, stdout, stdin=None, incar={}, overwrite=True):

        from os.path import join, exists, getsize
        import shutil
        import os

        # restart from previous calculation % 
        if stdin is not None:

            # udpate the structure % 
            self.load_structure(vasp,stdin)

            if stdin != stdout:
                if not exists(stdout): os.makedirs(stdout)
                overwrite = True

                # copy chgcar %
                chgin = join(stdin,'CHGCAR')
                chgout = join(stdout,'CHGCAR')
                if exists(chgin) and getsize(chgin):
                    if 'icharg' not in incar:
                        incar['icharg'] = 1
                elif 'icharg' not in incar:
                    incar['icharg'] = 2
                elif incar['icharg'] == 11:
                    raise IOError('CHGCAR not exists!')

                if incar['icharg'] == 1 or incar['icharg'] == 11:
                    if 'lcharg' in incar and incar['lcharg'] == False:
                        if exists(chgout): os.remove(chgout)
                        os.symlink(chgin,chgout)
                    else:
                        shutil.copyfile(chgin,chgout)

                # copy wavecar %
                wavein = join(stdin,'WAVECAR')
                waveout = join(stdout,'WAVECAR')
                if exists(wavein) and getsize(wavein):
                    if 'istart' not in incar:
                        incar['istart'] = 1
                else:
                    incar['istart'] = 0

                if incar['istart'] == 1:
                    if 'lwave' in incar and incar['lwave'] == False:
                        if exists(waveout): os.remove(waveout)
                        os.symlink(wavein,waveout)
                    else:
                        shutil.copyfile(wavein,waveout)

        incar = vasp.set_input(vasp.structure, stdout, overwrite, incar)
        return incar





