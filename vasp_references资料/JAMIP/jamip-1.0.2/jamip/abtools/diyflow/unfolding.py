import os
import numpy as np
from .miniflow import MiniFlow
from os.path import exists,join

class Unfolding(MiniFlow):
 
    yaml = {'lorbit':11,
            'icharg':11,
            'lwave': True,
            'mesh': 0.01,
            'encut': 520
           }

    def __init__(self,func,stdin=None,rootdir=None,*args,**kwargs):
        MiniFlow.__init__(self,func,stdin,rootdir)
        stdout = join(self.rootdir,'electric','unfolding')
        self.diy_calculator(func,stdout=stdout,stdin=stdin)

    def diy_calculator(self,func,stdout,stdin=None):
        from jamip.abtools.vasp.check import CheckStatus

        check = CheckStatus(self.rootdir)

        if not os.path.exists(stdout):
            os.makedirs(stdout)

        # finish_flag %

        # unfolding band %
        self.band_calculation(func,stdout,stdin)
        print('unfolding calculation finished')

        # update task status %
        status = check.success(join(stdout,'OUTCAR'), 'unfolding')
        if status['success'] and self.check(self.rootdir):
            func.tasks.diy.unfolding.finish = True
        else:
            status['success'] = False
        check.write_status(status,stdout)
            

    def band_calculation(self,vasp,stdout,stdin=None):
        from copy import deepcopy

        params = vasp.tasks.diy.unfolding
        # get params from stdin %
        if "nband" not in params:
            params["nband"] = self.get_nband(vasp,stdin)
        if "encut" not in params:
            params["encut"] = 520

        if not self.encut_enough(stdin,params['encut']):
            scf = deepcopy(params)
            scf['icharg'] = 2
            scf['istart'] = 1
            scf['lcharg'] = True
            scf['lwave'] = True
            stdin = self.calculator(vasp, stdout, stdin, incar=scf)

        # get primcell and kpath %
        kpts,gpts,kpath = self.get_unfolding_kpath(vasp,stdin,params)
        bandvasp = deepcopy(vasp)
        bandvasp.kpoints = kpath
        bandvasp.write_kpoints(stdout,'KPATH.in')
        bandvasp.kpoints = ("Reciprocal",gpts)
        bandvasp.write_kpoints(stdout,'GPOINTS')
        bandvasp.kpoints = ("Reciprocal",kpts)

        # loop the kpoints % 
        self.calculator(bandvasp, stdout, stdin, incar=params)

    @classmethod
    def create(self,params):
        from jamip.abtools.base.tasks import Incar
 
        data = Incar('unfolding',self.yaml)

        if 'dim' in params:
            # input primivate cell %
            if 'primcell' not in params:
                raise KeyError("primcell path is necessary if dim is given!")
            elif os.path.exists(params['primcell']):
                data.primcell = params.pop('primcell')
            
            dim = params.pop('dim').split()
            if len(dim) == 3:
                data.dim = np.diag(np.array(dim,dtype=int))
            elif len(dim) == 9:
                data.dim = np.array(dim,dtype=int).reshape(3,3)
        data.update(params)
        data.mesh = params.pop('mesh')
        return data

    @classmethod
    def check(self,path):
        if os.path.basename(path) != 'unfolding':
            file = join(path,'electric','unfolding','KPATH.in')
        else:
            file = join(path,'KPATH.in')
        if exists(file):
            print('Band unfolding calculation finish.')
            return True
        else:
            return False
   
    def encut_enough(self,stdin,energy):
        from jamip.analysis.vasp.outcar import GrepOutcar

        # get encut from scf calculation %
        if stdin != None and os.path.exists(stdin):
            encut = GrepOutcar().encut(stdin)
            if encut >= energy:
                return True
        else:
            raise OSError('encut grep filed.')

        return False

    def get_unfolding_kpath(self,vasp,stdin,params):
        from jamip.utils.brillouin_zone import HighSymmetryKpath
        from jamip.abtools.base.kpoints import __KPATH__, __KPT__
        from jamip.structure import read
        import spglib

        # supercell %
        cell = self.load_structure(vasp,stdin).bandStructure()

        # prim %
        if hasattr(params,'dim'):
            primcell = read(params.primcell).bandStructure()
            trans = params.dim
        else: 
            primcell = spglib.find_primitive(cell)
            trans = np.dot(np.linalg.inv(cell[0]),primcell[0])

        if 'band' in vasp.kpath:
            band = vasp.kpath['band'].kpoints
        else:
            band = self.get_band_kpath(vasp,stdin)

        # kpts %
        kpts = []
        insert = []
        for key, kp in band.split():
            kpt = self.kpath2kpt(kp.kpath[0].position,kp.kpath[1].position, primcell[0], params.mesh)
            kpts.extend(kpt)
            insert.append(len(kpt))
        insert.append(1)

        K = np.dot(kpts,trans.T)
        G = np.rint(K).astype(int)
        kpts = np.round(K-G, 6)
        band.insert = insert

        return kpts,G, band

    def kpath2kpt(self,kp1,kp2,lattice,mesh=None):
        import numpy.linalg as nlg
        step = np.subtract(kp2, kp1)
        if mesh == None:
            mesh=self.yaml['mesh']
        step_num = np.ceil(nlg.norm(np.dot(nlg.inv(lattice),step))/mesh).astype(np.int)
        kpath = [kp1 + step / step_num * nk
                 for nk in range(step_num)]

        return kpath

    @classmethod
    def plot(self,path,dim=None,primcell=None,smear=False):
        from jamip.analysis.vasp.outcar import GrepOutcar
        from jamip.analysis.vasp.wavecar import GrepWavecar
        from jamip.analysis.vasp.band import Kpath
        from jamip.utils.plot import Figure,BAND_EMIN,BAND_EMAX
        from jamip.structure import read
        import matplotlib.pyplot as plt
        import spglib

        if exists(join(path,'.status')):
            path = join(path,'electric','unfolding')
        if not self.check(path):
            raise OSError('Band unfolding calculation Failed!')

        # fermi %
        fermi = GrepOutcar().fermi_energy(path)
        cell = read(join(path,'CONTCAR')).bandStructure()
        if dim is not None:
            trans = np.asarray(dim)
            primcell = read(primcell).bandStructure()
        else:
            primcell = spglib.find_primitive(cell)
            trans = np.dot(np.linalg.inv(cell[0]),primcell[0])

        # wavecar
        w = GrepWavecar(path)
        w.wavecar()
        w.trans = np.dot(np.linalg.inv(primcell[0]),cell[0])
        K,G = w.read_unfolding()
        # spectral-weight %
        if exists('sw.npy'):
            sw = np.load('sw.npy')
        else:
            sw = w.spectral_weight(G)
            np.save('sw.npy',sw)
        # kpath-in %
        kpath,index = Kpath.read_kpath(path)
        delta = np.linalg.norm(np.mat(np.diff(K, axis=0))* np.mat(w.rec_cell)* np.mat(w.trans), axis=1)
        xkpt = np.concatenate(([0,], np.cumsum(delta)))

        if 'unfolding' in Figure.styles: 
            Figure().figure('unfolding')
        else:
            Figure().figure('band')

        plt.ylabel('Energy (eV)')
        plt.xlim(0,xkpt[-1])
        plt.ylim(BAND_EMIN,BAND_EMAX)
        xticks = []
        # plot kpoint symbols %
        for i in index[:-1]:
            xticks.append(xkpt[i])
            if i == 0: continue
            plt.axvline(xkpt[i],c='black')
        xticks.append(xkpt[-1])
        ax = plt.gca()
        ax.set_xticks(xticks)
        ax.set_xticklabels(kpath)

        # plot band.png %
        if smear:
            e0, sf = w.spectral_function(sw,nedos=4000,sigma=0.01)
            e0 -= fermi
            r0,r1 = np.sum(e0 < -3) , np.sum(e0 < 3)
            e0 = e0[r0:r1]
            sf = sf[:,r0:r1]
            # datamap %
            sfm = np.mean(sf) 
            sf[np.where(sf > sfm*10)] = sfm*10
            sf[np.where(sf > sfm/10)] = sfm/10 + np.log(sf[np.where(sf > sfm/10)]/sfm*10)
            X, Y = np.meshgrid(xkpt, e0)
            for i in range(w.nspin):
                ax.contourf(X, Y, sf[i], cmap='jet')
        else:
            for i in range(w.nspin):
                for nb in range(w.nbands):
                    plt.scatter(xkpt,w.bands[i,:,nb]-fermi,
                                s=sw[i,:,nb]*30 ,c='b')
