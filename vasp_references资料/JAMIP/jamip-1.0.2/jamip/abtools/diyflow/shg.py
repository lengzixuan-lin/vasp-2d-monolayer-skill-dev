import os
import numpy as np
from .miniflow import MiniFlow

class Shg(MiniFlow):
 
    yaml = {'ismear': 0,
            'istsrt': 1,
            'icharg': 11,
            'lwave': True,
            'loptics': True,
            'nedos': 3001,
            'emin': 0,
            'emax': 6,
            'enum': 301, 
            'expgap': None,
            'direction': 333
           }

    def __init__(self,func,stdin=None,rootdir=None,*args,**kwargs):
        MiniFlow.__init__(self,func,stdin,rootdir)
        stdout = os.path.join(self.rootdir,'optic','shg')
        self.diy_calculator(func,stdout=stdout,stdin=stdin)

    def diy_calculator(self,func,stdout,stdin=None):
        from os.path import join, exists
        from jamip.abtools.vasp.check import CheckStatus

        check = CheckStatus(self.rootdir)

        if not exists(stdout):
            os.makedirs(stdout)

        # finish_flag %
        if self.check(self.rootdir) and check.update_status(task='shg'):
            func.tasks.diy.shg.finish = True
            return

        # optics check %
        optics = None
        if func.tasks.optic != None and 'optics' in func.tasks.optic:
            if func.tasks.optic.optics.finish:
                optics = True
        if optics != True:
            print('optics calcuiation is unfinished, start shg calculation!')
        elif not exists(join(self.rootdir,'optic','optics','momentummatrix')):
            print("optics calcuiation don't output shg-matrix, start shg calculation!")
            optics = False
            
        # stdin %
        if optics is True:
            stdin = join(self.rootdir,'optic','optics')
        else:
            stdin = self.optics_calculation(func,stdout,stdin)

        # shg %
        self.shg_calculation(func,stdout,stdin)

        # update task status %
        status = {'task':'shg',
                  'finish': True,
                  'success': self.check(self.rootdir)
                 }
        check.write_status(status, stdout)
        func.tasks.diy.shg.finish = True

    def optics_calculation(self,vasp,stdout,stdin=None):
        from copy import deepcopy

        self.calculator(vasp, stdout, stdin, incar=vasp.tasks.diy.shg)
        return stdout

    def shg_calculation(self,vasp,stdout,stdin):
        from os.path import exists,join

        if not exists(stdout):
            os.makedirs(stdout)
        os.chdir(stdout)

        params = vasp.tasks.diy.shg
        shg = SHG_calculator(stdin)
        shg.prepare()
        shg.run(abc=params.direction,
                emin=params.emin,
                emax=params.emax,
                enum=params.enum,
                expgap=params.expgap)

        os.chdir(self.rootdir)


    @classmethod
    def check(self,root):
        from os.path import join,exists,getsize
        import re
        shgdir = join(root,'optic','shg')
        if not exists(shgdir):
            return False

        files = []
        for file in os.listdir(shgdir):
            if re.match('SHG_[0-9]{3}.dat',file):
                files.append(file)

        if len(files):
            print('SHG calculation finish.')
            return True
        else:
            return False

    @classmethod
    def create(self,params):
        '''
        '''

        from jamip.abtools.base.tasks import Incar
        import re
 
        yaml = {'npar': 1,
                'istsrt': 1,
                'icharg': 11,
                'lwave': True,
                'loptics': True,
                'nedos': 3001,
               }


        # jdos params %
        data = Incar('shg', yaml)
        if 'direction' in params:
            direction = np.array(re.findall('[1-3]',str(params.pop('direction'))),dtype=int)
            assert len(direction) == 3
            data.direction = direction - 1
        else:
            raise KeyError('Need direction params for shg calculation!')
        if 'emax' in params :
            data.emax = params.pop('emax')
        else:
            data.emax = 6
        if 'emin' in params: 
            data.emin = params.pop('emin')
        else:
            data.emin = 0
        if 'enum' in params:
            data.enum = params.pop('enum')
        else:
            data.enum = 301
        if 'expgap' in params:
            data.expgap = params.pop('expgap')
        else:
            data.expgap = None

        data.update(params)
        return data


class SHG_calculator:

    datafile = 'momentummatrix'
    
    def __init__(self, stdin=None):
        self.stdin = stdin

    def prepare(self):
        from jamip.analysis.vasp import BandFinder

        # jamip module %
        bf = BandFinder(self.stdin)
        self.nb = bf.get_info('nbands')
        self.nk = bf.get_info('nkpts')
        self.band = bf.get_bands()[0]
        self.bandgap = bf.get_bandgap()['indirect']
        self.vband,self.cband = np.array(bf.get_cbvb()[0])
        self.sigma = bf.get_info('sigma') 
        # zt %
        volume = bf.get_info('volume') * 6.7480546
        ispin = bf.get_info('ispin')
        with open('IBZKPT','r') as f:
            weights = []
            for i in range(3):
                f.readline()
            for line in f:
                weights.append(line.split()[-1])
        k_weight_sum = np.sum(np.array(weights,dtype=float))
        self.zt = 2 / ispin / volume / k_weight_sum
        # main data %
        self.data = self.read_matrix()

    def read_matrix(self):
        path = os.path.join(self.stdin,self.datafile)
        with open(path,'rb') as f:
            data = np.fromfile(f, dtype=np.complex128)
            data = data.reshape(self.nk,3,self.nb,self.nb).transpose(0,3,2,1)
        return data

    def run(self,**kwargs):
        import multiprocessing
    
        global a,b,c
        h2ev = 27.211338386
        a,b,c = kwargs['abc']
        Emin = kwargs['emin'] / h2ev
        Emax = kwargs['emax'] / h2ev
        Enum = kwargs['enum']
        if 'expgap' in kwargs and kwargs['expgap'] != None:
            self.scissor = (kwargs['expgap'] - self.bandgap) / h2ev
        else:
            self.scissor = 0 
        self.Energy = np.linspace(Emin, Emax, Enum) 
        self.eta = self.sigma / h2ev * 1j
        params = []

        for ik in range(self.nk):
            pmat = self.data[ik] 
            band_ik = self.band[ik,:,0] / h2ev
            ztm = np.zeros((3,3)).astype(np.complex128)
        
            for vb in range(0,self.vband):
                for cb in range(self.cband,self.nb):
                    Ecv = band_ik[cb] - band_ik[vb]
                    pmat[vb,cb] *= (Ecv + self.scissor) / Ecv
        
            params.append((pmat,band_ik))

        # parallel map %
        p = multiprocessing.Pool()
        res = p.map(self.func, params)
        p.close()
        p.join()
        
        # unit transform %
        shg = np.sum(res,axis=0) * self.zt
        output = 'SHG_%d%d%d.dat' %(a+1,b+1,c+1)
        with open(output,'w') as f:
            for e,real,imag,absolute in zip(self.Energy*h2ev,np.real(shg),np.imag(shg),np.abs(shg)):
                f.write('{0:>12.6f}{1:>12.6f}{2:>12.6f}{3:>12.6f}\n'.format(e,real,imag,absolute))

    @staticmethod
    def transform(value):
        if abs(value) > 1e-4:
            return 1/value
        else:
            return value * 1e8

    def func(self,args):

        pmat,band = args
        ztm = np.zeros((3,3)).astype(np.complex128)
        shg = np.zeros_like(self.Energy).astype(np.complex128)
 
        for vb in range(0,self.vband):
            for cb in range(self.cband,self.nb):
                Ecv = band[cb] - band[vb] + self.scissor
                Vvc = pmat[cb,vb]
                _Vvc = Vvc.conjugate()
                dcv = pmat[cb,cb] - pmat[vb,vb]
                chiw = 0
                chi2w = 0
 
                for ib in range(self.nb):
                    if ib in [vb,cb]: continue
                    Eiv = band[ib] - band[vb]
                    Eic = band[ib] - band[cb]
                    if ib > self.vband:
                        Eiv += self.scissor
                    else:
                        Eic -= self.scissor
                    Vci = pmat[ib,cb]
                    Viv = pmat[vb,ib]
                    _Vci = Vci.conjugate()
                    _Viv = Viv.conjugate()
 
                    coef = self.transform(Ecv * Eiv * Eic * (Eiv+Eic))
                    ztm[0,0] = _Vvc[a] * (_Vci[b]*_Viv[c] + _Viv[b]*_Vci[c]) * coef
 
                    coef = self.transform(Ecv * Eiv * Eic * (Ecv+Eiv)) * 0.5
                    ztm[0,1] = Vci[c] * (Vvc[a]*Viv[b] + Viv[a]*Vvc[b]) * coef
 
                    coef = self.transform(Ecv * Eiv * Eic * (Ecv-Eic)) * 0.5
                    ztm[0,2] = Viv[b] * (Vvc[a]*Vci[c] + Vci[a]*Vvc[c]) * coef
 
                    coef = self.transform(Ecv**3 * -Eiv * Eic) * 0.5
                    ztm[1,0] = (Eiv * Viv[b] * (Vvc[a]*Vci[c] + Vci[a]*Vvc[c]) +
                                Eic * Vci[c] * (Vvc[a]*Viv[b] + Viv[a]*Vvc[b])) * coef

                    coef = self.transform(Ecv**3 * Eiv * -Eic / (Eiv+Eic))
                    ztm[1,2] = _Vvc[a] * (_Vci[b]*_Viv[c] + _Viv[b]*_Vci[c]) * coef
 
                    coef = self.transform(Ecv**3 * -Eiv * Eic) *-0.5 * Eiv
                    ztm[2,0] = Vci[a] * (Vvc[b]*Viv[c] + Viv[b]*Vvc[c]) * coef
 
                    coef = self.transform(Ecv**3 * -Eiv * Eic) * 0.5 * Eic
                    ztm[2,1] = Viv[a] * (Vci[b]*Vvc[c] + Vvc[b]*Vci[c]) * coef
 
                    chi2w += ztm[0,0] + ztm[1,2]
                    chiw += -ztm[0,1]+ztm[0,2]+ztm[1,0]+(ztm[2,0]-ztm[2,1])*0.5
 
                ztm[1,1] = 4 * _Vvc[a] * (Vvc[b]*dcv[c] + dcv[b]*Vvc[c]) / Ecv**4
                ztm[2,2] = 0.5 * Vvc[a] * (Vvc[b]*dcv[c] + dcv[b]*Vvc[c]) / Ecv**4
 
                # chi2w %
                shg += (chi2w + ztm[1,1]) / (Ecv-2*self.Energy+self.eta)
                # chiw %
                shg += (chiw + 0.5*ztm[2,2]) / (Ecv-self.Energy+self.eta)
 
        return shg

    def plot(self,path):
        import matplotlib
        matplotlib.use('agg')
        import matplotlib.pyplot as plt
        from os.path import isfile,isdir,basename,join
        import re

        files = []
        if isfile(path):
            if re.match('SHG_[0-9]{3}.dat',basename(path)):
                files.append(path)
        elif isdir(path):
            for file in os.listdir(path):
                if re.match('SHG_[0-9]{3}.dat',file):
                    files.append(join(path,file))

        if len(files) == 0:
            raise OSError('SHG datafile not exists!')

        for file in files:
            with open(file,'r') as f:
                data = []
                for line in f:
                   data.append(line.split())
            
                data = np.array(data,dtype=float)
               
                plt.figure(figsize=(10,6))
                plt.plot(data[:,0],data[:,1],label='real')
                plt.plot(data[:,0],data[:,2],label='imag')
                plt.plot(data[:,0],data[:,3],label='abs')
                plt.xlim(0,5)

                pngname = basename(file).split('.')[0] + '.png'
                plt.savefig(pngname)

