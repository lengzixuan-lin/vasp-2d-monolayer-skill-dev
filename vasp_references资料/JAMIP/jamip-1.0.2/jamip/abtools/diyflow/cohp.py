import os
import numpy as np
from .miniflow import MiniFlow

class Cohp(MiniFlow):
 
    yaml = {'COHPstartEnergy': -20,
            'COHPendEnergy': 10,
            'basisset': 'pbeVaspFit2015',
            'basisfunctions': [None,],
            'AtomsIndex': None}

    def __init__(self,func,stdin=None,rootdir=None,*args,**kwargs):
        MiniFlow.__init__(self,func,stdin,rootdir)
        stdout = os.path.join(self.rootdir,'electric','cohp')
        self.diy_calculator(func,stdout=stdout,stdin=stdin)

    def diy_calculator(self,func,stdout,stdin=None):
        from os.path import join, exists
        from jamip.abtools.vasp.check import CheckStatus

        check = CheckStatus(self.rootdir)

        if not exists(stdout):
            os.makedirs(stdout)

        # finish_flag %
        if self.check(self.rootdir):
            func.tasks.diy.cohp.finish = True
            return

        # dos %
        self.dos_calculation(func,stdout,stdin)

        # lobster %
        self.cohp_calculation(func,stdout)

        # update task status %
        status = check.success(join(stdout,'OUTCAR'),'cohp')
        if self.check(self.rootdir):
            func.tasks.diy.cohp.finish = True
        else:
            status['success'] = False
        check.write_status(status, stdout)


    def dos_calculation(self,vasp,stdout,stdin=None):
        from os.path import join, exists, dirname
        from jamip.abtools.vasp.check import CheckStatus
        from copy import deepcopy

        check = CheckStatus(self.rootdir)

        dosvasp = deepcopy(vasp)
        if dosvasp.model not in ['Monkhorst-pack','Gamma']:
            dosvasp.kpoints = 'G', '2 2 2'
        # loop the kpoints % 
        self.calculator(dosvasp, stdout, stdin, incar=vasp.tasks.diy.cohp)

    def cohp_calculation(self,vasp,stdout):

        params = vasp.tasks.diy.cohp
        # write lobsterin %
        with open(os.path.join(stdout,"lobsterin"),'w') as f:
            line = '{0:16} {1}\n'
            f.write(line.format('basisSet',params.set))
            f.write(line.format('COHPstartEnergy',params.start))
            f.write(line.format('COHPendEnergy',params.end))
            for lm in params.func:
                f.write(line.format('basisfunctions',lm))
            f.write('\ncohpbetween atom {0[0]} and atom {0[1]} orbitalwise'.format(params.atom))
       
        os.chdir(stdout)
        os.popen("lobster > lobster.log").readline()
        os.chdir(self.rootdir)

    @classmethod
    def check(self,path):
        from os.path import join,exists,basename
        if basename(path) != 'cohp':
            file = join(path,'electric','cohp','lobsterout')
        else:
            file = join(path,'lobsterout')
        if exists(file):
            with open(file,'r') as f:
                for line in f:
                    if line.startswith('finished'):
                        print('COHP calculation finish.')
                        return True
        return False

    @classmethod
    def create(self,params):
        '''
        default cohp parameters
        COHPstartEnergy  -20
        COHPendEnergy     10
        basisfunctions S  3s 3p
        basisfunctions Mo 4p 4d 5s
        cohpGenerator from 1.4 to 1.5 type Ga type Sr
        '''
        from jamip.abtools.base.tasks import Incar
 
        yaml = {'nedos': '3001',
                'isym' : -1,
                'lorbit': 12,
                'lwave': True,
                'icharg': 1,
                'nsw': 0
               }

        data = Incar('cohp',yaml)

        # cohp necessary params %
        try:
            data.func = params.pop('basisfunctions')
            data.atom = params.pop('AtomsIndex').split()
        except:
            raise KeyError("Missing necessary params for COHP! task exit")
        # cohp params %
        if 'COHPstartEnergy' in params:
            data.start = params.pop('COHPstartEnergy')
        else:
            data.start = -20
        if 'COHPendEnergy' in params:
            data.end = params.pop('COHPendEnergy')
        else:
            data.end = 10
        if 'basisSet' in params:
            data.set = params.pop('basisSet')
        else:
            data.set = "pbeVaspFit2015"

        data.update(params)
        return data

    @classmethod
    def plot(self,path):
        from os.path import join,exists
        from jamip.utils.plot import Figure
        import matplotlib.pyplot as plt
        import re
        
        if exists(join(path,'lobsterin')):
            stdin = path
        elif exists(join(path,'.status')) and exists(join(path,'electric','cohp','lobsterin')):
            stdin = join(path,'electric','cohp')
        else:
            raise OSError('Cannot find cohp calculation!')
 
        if not self.check(stdin):
            raise OSError('COHP calculation unfinished!')

        # read elements and obrits %
        with open(join(stdin,'lobsterin'),'r') as f:
            atoms = {}
            for line in f:
                if line.startswith('basisfunctions'):
                    line = line.split()
                    atoms[line[1]] = line[2:]

        # read coopcar %
        with open(join(stdin,'COOPCAR.lobster'),'r') as f:
             f.readline()
             row, _, points, emin, emax, efermi = f.readline().split()
             labels = []
             for i in range(int(row)):
                 labels.append(f.readline())
                 #result = re.findall('\d:([A-z][a-z]?[0-9]+)',f.readline())
             coop = []
             for i in range(0,int(points)):
                 coop.append(f.readline().split())
             coop = np.array(coop,dtype=float)

        # plot %     
        if 'cohp' in Figure.styles:
            fig = Figure().figure('cohp')
        else:
            fig = Figure().figure('dos')
        plt.xlim(-6,4)
        plt.ylim(-0.4,0.4)
        energy = coop[:,0]
        data = {}
        for i,label in enumerate(labels):
            elms = re.findall('([A-Z][a-z]?[0-9]+)',label)
            orbs = re.findall('\[([0-9]+[spdf])\w*\]',label)
            if len(elms) == 0: continue
            if len(orbs) == 0:
                label = '{0[0]}-{0[1]}'.format(elms)
            else:
                label = '{0[0]}$_{{{1[0]}}}$-{0[1]}$_{{{1[1]}}}$'.format(elms,orbs)
            if label not in data:
                data[label] = coop[:,2*i+1]
            else:
                data[label]+= coop[:,2*i+1]
        for label,ydata in data.items():
            plt.plot(energy,ydata,label=label)

        plt.xlabel("Energy")
        plt.ylabel("n(e)")
        plt.legend(loc=0,frameon=True)

                 








 
