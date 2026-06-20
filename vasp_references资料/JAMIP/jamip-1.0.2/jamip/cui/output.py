import os
import numpy as np
from jamip.analysis.vasp import GrepOutcar


__task_dict__ = {'dielectric':('dielectric','dielectric_ionic'),
                 'cbvb':('bandgap','vbm-kpoint','cbm-kpoint'),
                 'bandgap':('bandgap','isdirect'),
                 'boltztrap':('e-mass','H-mass'),
                 'emass':('H-mass','e-mass'),
                 'format':('format',)}


class __OutputData(GrepOutcar):

    def __init__(self,*args,**kwargs):
        self.__plot = False
        self.__csv = False
        self.__sort = False
        self.__form = False
        self.__path = None

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self,value=None):
        from os.path import exists,join,isdir,isfile,dirname
        paths = []
        if exists(value) and isdir(value):
            if exists(join(value,'.status')):
                paths.append(value)
            elif exists(join(value,'OUTCAR')):
                paths.append(value)
            else:
                for dir in os.listdir(value):
                    if exists(join(value,dir,'.status')):
                        paths.append(join(value,dir))
        elif isfile(value):
            import pickle
            try:
                root = dirname(value)
                with open(value,'rb') as f:
                    pool=pickle.load(f)
                for dir in pool.keys():
                    if exists(join(root,dir,'.status')):
                        paths.append(join(root,dir))
            except:
                print('PathError: Invalid poolfile')
                
        else:
            print('PathError: Invalid directory')
        self.__path = paths
        print('Total = %s' %len(paths))

    def set_params(self,params=None):
        self.tasks = []
        for i in params:
            if i == 'plot':
                self.__plot = True
            elif i == 'csv':
                self.__csv = True
            elif i == 'sort':
                self.__sort = True
            elif i == 'form':
                self.__form = True
            else:
                self.tasks.append(i)

    def run(self,params,path=None,**kwargs):
        # update params %
        self.set_params(params['output'])
        if 'pool' in params:
            self.path = params['pool']
        elif path == None:
            self.path = os.getcwd()
        elif os.path.exists(path):
            self.path = path
        else:
            print('Warning! Invalid input path')

        # load datas %
        if len(self.tasks):
            dataset = self.getdatas()
        else:
            print('Warning! No vaild task was found')

        # run main_project %
        if self.__plot:
            self.plot(dataset)
        if self.__csv:
            self.csv(dataset)
        elif self.__sort:
            self.sort(dataset)
        elif self.__plot is False or self.__form:
            self.form(dataset)

    def getdatas(self):
        import pandas as pd

        # basename %
        dataset = []
        dat = [os.path.basename(i) for i in self.path]
        dataset.append(pd.DataFrame(dat, columns=['path'], index=self.path))

        # property
        for task in self.tasks:

            # check whether vaild task %
            state = self.find_task_belong(task)
            if state == 0:     # Invaild task %
                print('Invaild_task: %s' %task)
                continue
        
            # Vaild task %
            dat = []
            success = 0
            func = getattr(self,task)
            # run all path %
            for path in self.path:
                try:
                    scfdir = os.path.join(path,'scf')
                    # GrepOutcar moudle %
                    if state == 2 and os.path.exists(scfdir)  :
                        dat.append(func(scfdir))
                    # local moudle %
                    else:
                        dat.append(func(path))
                    success+=1
                except:
                    print('IOError: read %s task-%s failed' %(path,task))
                    dat.append(None) 
                
            # conclusion %
            print('%s success = %d' %(task,success))

            if state == 1:
                tasks = __task_dict__[task]
                null = [None]*len(tasks)
                for i,v in enumerate(dat):
                    if v == None:
                        dat[i] = null
            else:
                tasks = [task]
                        
            dataset.append(pd.DataFrame(dat, columns=tasks, index=self.path))
        dataset = pd.concat(dataset,axis=1)
        return dataset

    def find_task_belong(self, meth_name):
        '''check whether task belong to main_class or sub_class
           return 0 : Invalid task
           return 1 : belong to main_class, path use main_director
           return 2 : belong to sub_class, path use stdin/scf'''

        for ty in type(self).mro():
            if meth_name in ty.__dict__:
                if ty == type(self):
                    return 1
                else:
                    return 2
        return 0 

    def format(self,path):
        '''Structure format'''
        from jamip.analysis.vasp import Finder
        format = sep = ''
        if self.__csv: 
            sep = ' '
        for elm,num in Finder(path).grep('atominfo'):
            if num != 1:
                format += '%s%d%s' %(elm,num,sep)
            else:
                format += '%s%s' %(elm,sep)
        return format.rstrip()
            
    def dielectric(self,path):
        '''dielectric dielectric_ionic'''
        from jamip.analysis.vasp import OpticsFinder
        of = OpticsFinder(path)
        diel_e = np.round(of.get_dielectric_const(),6)
        diel_ion = np.round(of.get_dielectric_const_of_ionic(),6)
        return diel_e,diel_ion

    def cbvb(self,path):
        '''cbvb data'''
        from jamip.analysis.vasp import BandFinder
        bf = BandFinder(path)
        cbmvbm = bf.get_cbmvbm()
        bandgap = np.around(cbmvbm['cbm']['energy'] - cbmvbm['vbm']['energy'],4)
        cbm_kpoint = '{0[0]}, {0[1]}, {0[2]}'.format(np.round(cbmvbm['cbm']['kpoint'],6))
        vbm_kpoint = '{0[0]}, {0[1]}, {0[2]}'.format(np.round(cbmvbm['vbm']['kpoint'],6))
        return bandgap,cbm_kpoint,vbm_kpoint

    def bandgap(self,path):
        '''bandgap isdirect'''
        from jamip.analysis.vasp import BandFinder
        bf = BandFinder(path)
        gap = bf.get_bandgap()
        isdirect = False if gap['direct'] > gap['indirect'] else True
        return gap['indirect'],isdirect

    def boltztrap(self,path):
        dat = os.path.join(path,'diy','boltztrap','boltztrap.dat')
        if os.path.exists(dat):
            with open(dat,'r') as f:
                lines = f.readlines()
            assert lines[5].split()[-1] == "e_mass"
            assert lines[6].split()[-1] == "H_mass"

            e_mass = lines[5].split()[0]
            H_mass = lines[6].split()[0]
            return e_mass,H_mass
        return None

    def emass(self,path):
        '''H-mass e-mass'''
        from jamip.analysis.vasp import BandFinder
        bf = BandFinder(path)
        emass = bf.get_emass()
        cbm_emass = np.around(np.cbrt(emass['cbm-x']*emass['cbm-y']*emass['cbm-z']),3)
        vbm_emass = np.around(np.cbrt(emass['vbm-x']*emass['vbm-y']*emass['vbm-z']),3)
        return cbm_emass,vbm_emass

    def csv(self,dataset):
        from os.path import basename,dirname
        import pandas as pd
        if len(self.path) > 1:
            filename = basename(dirname(self.path[0]))+'.csv'
        else:
            filename = basename(self.path[0])+'.csv'
        dataset.to_csv(filename,index=False)

    def plot(self,dataset):
        '''
        simple plot model 
        plot up to 2 properties
        x-axis is sorted-index, only plot datas not None 
        if index <= 10 , x_params is path
        else, plot hist
        '''
        from os.path import split
        import matplotlib
        matplotlib.use('agg')
        import matplotlib.pyplot as plt
        import pandas as pd
        path = np.array([split(p)[-1] for p in self.path])
        # task 1 %
        task = dataset.keys()[0]
        index = np.where(~pd.isna(dataset[task]))
        xlen = len(index[0])
        if xlen > 10:
            pass
        elif xlen <= 10 and xlen > 0:
            fig,ax1=plt.subplots(figsize=(6,6))
            plt.figure(figsize=(6,6))
            plt.plot(range(xlen),np.array(dataset[task])[index],'o',c='b')
            plt.xticks(range(xlen),path[index],rotation=30)
        # task 2 %
        if len(dataset.keys()) > 1:
            task = dataset.keys()[1]
            index = np.where(~pd.isna(dataset[task]))
            xlen = len(index[0])
            if xlen > 10:
                pass
            elif xlen <= 10 and xlen > 0:
                ax2 = ax1.twinx()
                plt.plot(range(xlen),np.array(dataset[task])[index],'^',c='orange')
                plt.xticks(range(xlen),path[index],rotation=30)
        plt.savefig('output.png')           

    def sort(self,dataset):
        from os.path import split
        def title(task):
            print('\n+'+'-'*(len(task)+12)+'+')
            print('| Property: %s |' %task)
            print('+'+'-'*(len(task)+12)+'+')

        for task in dataset.keys():
            if dataset[task].dtypes != object: 
                title(task)
                for i,v in zip(np.argsort(dataset[task]),np.sort(dataset[task])):
                    print(' %s, %s' %(split(self.path[i])[-1],v))

    def form(self,dataset):
        from jamip.utils.views import shellform
        # init lists %
        dataset = dataset.to_dict(orient='records')
        shellform(dataset)

