import os
import numpy as np
from .miniflow import MiniFlow

class Hse_band(MiniFlow):

    yaml = {'icharg': 11,
            'lorbit': 11,
            'mesh': 0.01} 

    def __init__(self,func,stdin=None,rootdir=None,*args,**kwargs):
        MiniFlow.__init__(self,func,stdin,rootdir)
        stdout = os.path.join(self.rootdir,'electric','hse_band')
        self.diy_calculator(func,stdout=stdout,stdin=stdin)

    def diy_calculator(self,func,stdout,stdin=None):
        from os.path import join, exists, getsize
        from jamip.abtools.vasp.check import CheckStatus

        if not exists(stdout):
            os.makedirs(stdout)

        # hse %
        self.hse_calculation(func,stdout,stdin)

        # update task status %
        check = CheckStatus(self.rootdir)
        status = check.success(join(stdout,'OUTCAR'),'hse_band')
        if self.check(self.rootdir):
            func.tasks.diy.hse_band.finish = True
        else:
            status['success'] = False
        check.write_status(status,stdout)

    def hse_calculation(self,vasp,stdout,stdin=None):
        from os.path import join, exists, dirname
        from copy import deepcopy

        params = vasp.tasks.diy.hse_band
        self.yaml['mesh'] = params.mesh

        # step 1: set KPOINTS %
        hsevasp = deepcopy(vasp)
        if 'nband' not in params:
            params['nband'] = self.get_nband(vasp,stdin)
        kpts,kpath = self.get_kpath(vasp,stdin)
        hsevasp.kpoints = kpath
        hsevasp.write_kpoints(stdout,'KPATH.in')
        hsevasp.kpoints = ("Reciprocal",kpts)

        # step 2: calculate HSE gap %    	
        hsevasp._xc_.add('hse')
        self.calculator(hsevasp, stdout, stdin, incar=params)

    @classmethod
    def check(self,path):
        from os.path import join,exists,basename
        if basename(path) != 'hse_band':
            file = join(path,'electric','hse_band','KPATH.in')
        else:
            file = join(path,'KPATH.in')
        if exists(file):
            print('HSE-band calculation finish.')
            return True
        else:
            return False

    @classmethod
    def create(self,params):
        """
        """
        from jamip.abtools.base.tasks import Incar

        # boltztrap params %
        data = Incar('hse_band', self.yaml)
        if 'mesh' in params:
            data.mesh = params.pop('mesh')
        else:
            data.mesh = 0.01
        data.update(params)
        return data

    def get_kpath(self,vasp,stdin):
        from jamip.utils.brillouin_zone import HighSymmetryKpath
        from jamip.analysis.vasp import BandFinder

        # IBZKPT %
        bf = BandFinder(stdin)
        ibz = bf._get_kpoint(stdin,weight=True)
        structure = self.load_structure(vasp,stdin)

        if 'band' in vasp.kpath:
            band = vasp.kpath['band'].kpoints
        else:
            band = self.get_band_kpath(vasp,stdin)

        # kpts %
        kpts = []
        insert = []
        for k1, k2 in band.split():
            kpt = self.kpath2kpt(k1.position, k2.position, structure.lattice)
            kpts.extend(kpt)
            insert.append(len(kpt))
        insert.append(1)

        # merge %
        kpts = np.c_[kpts,np.zeros(len(kpts))]
        kpts = np.r_[ibz,kpts]
        band.insert = insert

        return kpts, band

    @classmethod
    def kpath2kpt(self,kp1,kp2,lattice,mesh=None):
        import numpy.linalg as nlg
        step = np.subtract(kp2,kp1)
        if mesh == None: 
            mesh=self.yaml['mesh']
        step_num = np.ceil(nlg.norm(np.dot(nlg.inv(lattice),step))/mesh).astype(np.int)
        kpath = [kp1 + step / step_num * nk
                 for nk in range(step_num)]

        return kpath

    @classmethod
    def plot(self,path):
        from jamip.analysis.vasp import BandFinder
        from jamip.analysis.vasp.band import Kpath
        from jamip.structure import read
        from jamip.utils.plot import Figure,BAND_EMIN,BAND_EMAX
        from os.path import exists,join
        import matplotlib.pyplot as plt

        if exists(join(path,'.status')):
            path = join(path,'electric','hse_band')
        if not self.check(path):
            raise OSError("HSE band calculation failed!")

        if 'hseband' in Figure.styles:
            Figure().figure('hseband')
        else:
            Figure().figure('band')
   
        # get main datas %
        bf = BandFinder(path)
        kpath,index = bf.read_kpath(path)
        kpoints = bf.get_kpoints()
        skip = len(kpoints) - index[-1] -1
        kpoints = kpoints[skip:]
        bands=bf.get_bands()[:,skip:]
        rec_vector = bf.get_info('reciprocal_lattice_vectors')

        # kpath-in %
        delta = [np.linalg.norm(np.dot(rec_vector,dk)) for dk in kpoints[1:]-kpoints[:-1] ]
        delta.insert(0,0)
        xkpt = np.cumsum(delta)
        xticks=[]
        for i in index:
            xticks.append(xkpt[i])
            if i == 0: continue
            plt.axvline(xkpt[i],c='black')
        ax = plt.gca()
        ax.set_xticks(xticks)
        ax.set_xticklabels(kpath)

        # add bandgap %
        cv = bf.get_cbmvbm(bands)
        if cv['gap'] > 0:
            shift = cv['vbm']['energy']
            # plot bandgap %
            xvbm = xkpt[cv['vbm']['index'][1]]
            xcbm = xkpt[cv['cbm']['index'][1]]
            Ecbm = cv['cbm']['energy']-cv['vbm']['energy']
            plt.scatter([xvbm],[0],color='r',s=40)
            plt.plot([max(0,xcbm-xkpt[-1]/100),min(xkpt[-1],xcbm+xkpt[-1]/100)],[Ecbm,Ecbm],color='r')
            plt.plot([xcbm,xcbm],[0,Ecbm],c='r',lw=2)
            xtext=[xcbm+xkpt[-1]/100,xcbm-xkpt[-1]/6][xcbm>xkpt[-1]*2/3]
            plt.text(xtext,Ecbm/2,'{:.3f} eV'.format(Ecbm))
        else:
            shift = bf.get_fermi()

        for bands_ispin in bands:
            ybands = bands_ispin[...,0] - shift
            plt.plot(xkpt,ybands,c='b')

        plt.ylim(BAND_EMIN,BAND_EMAX)
        plt.xlim(0,xkpt[-1])

