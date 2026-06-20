from ..base.tasks import Incar,Task

class TaskBuilder(object):

    _xc_ = ['soc','hse','gw']
    _task_ = {'electric':('dos','band','partchg','emass','born','stm','hse_gap'),
              'magnetic':('ferro','anti','ferri'),
              'optic':('optics','dielectric','gw','bse'),
              'phonon':('force','softmode','gruneisen'),
              'mechanic':('elastic','possion'),
             }

    def __init__(self, *args, **kwargs):

        self._data = None

    @property
    def diyflow(self):
        from jamip.abtools.diyflow import get_diy_modules
        return get_diy_modules()

    @property
    def property(self):
        return self._task_

    @classmethod
    def build(cls,tasks):
        from jamip.abtools.diyflow import get_diy_modules
        data = Task('vasp')
        # relax % 
        opt = ''
        for key in ['ions', 'shape', 'volume']:
            if key in tasks: opt += key[0]
        if len(opt):
            data['relax'] = opt
        elif 'relax' in tasks:
            data['relax'] = 'isv'

        # md %
        tmp = []
        for key in ['nvt', 'nve', 'npt']:
            if key in tasks:
                tmp.append(key)
        if len(tmp) == 1:
            data['md'] = tmp[0]
        elif len(tmp) > 1:
            raise ValueError('Only one molecular dynamics calculation at a time is supported.')   

        # scf %
        if 'scf' in tasks: 
            data['scf'] = ''

        # nonscf %
        for key, props in cls._task_.items():
            tmp = []
            for taskname in props:
                if taskname in tasks:
                    tmp.append(taskname)
            if len(tmp):
                data[key] = tmp

        # add xc_func %
        tmp = []
        for key in cls._xc_:
            if key in tasks:
                tmp.append(key)
        if len(tmp):
            data['xc'] = tmp

        # add diy-task if it exists in floder ~/abtools/diyflow
        tmp = []
        for module in get_diy_modules():
            if module in tasks:
                tmp.append(module)

        # converge-test
        for conv in ['kpoints_conv', 'cutoff_conv']:
            if conv in tasks:
                tmp.append(conv)

        if len(tmp):
            data['diy'] = tmp 
        
        return data
        
    @classmethod
    def create(cls,task,path,jobname):
        import os
        import warnings
        from os.path import dirname, join, relpath 
        from jamip.abtools.diyflow import import_diy_module
        from ruamel import yaml

        try:
            with open(join(path,'.incar')) as f:
                incarset = yaml.safe_load(f)
        except:   
            raise IOError("Failed in read incar.yaml !")

        data = Task('vasp',task)
        data._builder = cls

        # base % 
        if 'base' in incarset:
            data['base'] = Incar('base',incarset['base'])

        # relax % 
        if 'relax' in task and task['relax'] != None:
            isif = {'i':2, 'isv':3, 'is':4,'s':5, 'sv':6, 'v':7, 'iv':-1}
            params = {'nsw':50, 'isif':isif[task['relax']], 'ibrion':2}
            if 'relax' in incarset:
                params.update(incarset['relax'])
            data['relax'] = Incar('relax',params)
        else:
            params = {'nsw':50, 'isif':3, 'ibrion':2}
            data['relax'] = Incar('relax', params, finish=True)

        # md %
        if 'md' in task and task['md'] != None:
            params = {'isym':0, 'ibrion':0, 'lwave':False, 'lcharg':False}
            md = task['md']
            if md in incarset:
                params.update(incarset[md])
            data['md'] = Incar(md,params)

        # scf %
        if 'scf' in task and task['scf'] != None:
            params = {'isif':2, 'nsw':0, 'ibrion':-1}
            # scf will add value in future, and here will update 
            # dicts for different key
            if 'scf' in incarset:
                params.update(incarset['scf'])
            data['scf'] = Incar('scf',params)

        # xc_func %
        if 'xc' in task and task['xc'] != None:
            params = {}
            for func in task['xc']:
                if func not in cls._xc_: continue
                elif func in incarset:
                    params[func] = Incar(func,incarset[func])
                else:
                    if func != 'pe': 
                        print('Warning! no %s params ! ' %func)
                    params[func] = Incar(func)
               
            data['xc'] = Task('xc_func',params)

        # property %
        for key in cls._task_:
            params = {}
            if key in task and len(task[key]):
                if key == 'phonon':
                    if 'force' not in task['phonon']: 
                        task['phonon'].append('force')
                    for prop in task['phonon']:
                        if prop not in incarset: 
                            raise KeyError("Missing necessary params force!")
                        params[prop] = cls.phonon_create(prop,**incarset[prop])
                else:
                    for prop in task[key]:
                        if prop in incarset:
                            params[prop] = Incar(prop,incarset[prop])
                        else:
                            params[prop] = Incar(prop)
                data[key] = Task(key,params)

        # diyflow %
        if 'diy' in task and len(task['diy']):
            conv = {}
            params = {}
            for module in task['diy']:
                if module in ['kpoints_conv', 'cutoff_conv']:
                    diy_class = import_diy_module(module)
                    conv[module] = diy_class.create(incarset[module])

                elif module in incarset:
                    diy_class = import_diy_module(module)
                    params[module] = diy_class.create(incarset[module])
                 
                if len(params):
                    data['diy'] = Task('diy',params)
                if len(conv):
                    data['converge'] = Task('converge', conv)
                        
        # add %
        if 'electric' in data:
            if 'band' not in data['electric']:
                params = incarset['band'] if 'band' in incarset else None
                data['electric']['band'] = Incar('band',params,finish=True)
        if 'optic' in data:
            if 'electric' not in data:
                data['electric'] = Task('electric')
            if 'band' not in data['electric']:
                params = incarset['band'] if 'band' in incarset else None
                data['electric']['band'] = Incar('band',params,finish=True)

        # extra %
        try:
            with open(join(path,'.extra'),'r') as f:
                extraset = yaml.safe_load(f)
                if extraset != None and jobname in extraset:
                    data['extra'] = Incar('extra',extraset[jobname])
        except:
            print('no extra data')

        return data


    @classmethod
    def phonon_create(cls, task, parallel=1, dim='1 1 1', symprec=1e-5, **params):
        import numpy as np
        data = Incar(task)
        data.symprec = symprec
        data.parallel = parallel
        dim = np.array(dim.split(),dtype = int)
        if len(dim) == 3:
            data.dim = np.diag(dim)
        elif len(dim) == 9:
            data.dim = dim.reshape(3,3)

        if task == 'softmode':
            if 'amplitude' in params:
                data.amplitude = np.array(params.pop('amplitude').split(),dtype = float)
            if 'q' in params:
                data.q = np.array(params.pop('q').split(),dtype = float)
            if 'argument' in params:
                data.argument = params.pop('argument')
            if 'band_index' in params:
                data.band_index = params.pop('band_index')

        if task == 'gruneisen':
            if 'scale' in params:
                data.scale = params.pop('scale')
            else:
                data.scale = 0.05
            params['isif'] = 4
            params['ibrion'] = 2

        data.data = params
        return data

    @classmethod
    def set_force(cls,task,force):
        try:
            task['base']['ediffg'] = -float(force)
        except:
            if force != None:
                print('Warning! force should be float')

    @classmethod
    def set_energy(cls,task,energy):
        try:
            task['base']['ediff'] = float(energy)
        except:
            if energy != None:
                print('Warning! energy should be float')

class VaspIncar:

    _energy_ = 1E-5 
    _force_  = None 
    _cutoff_ = 1.3 
    _nbands_ = 1.2

    @property 
    def energy(self):
        return self._energy_
    
    @property
    def force(self):
        return self._force_ 

    @property
    def cutoff(self):
        return self._cutoff_
    
    @property
    def nbands(self):
        return self._nbands_
    
    @energy.setter
    def energy(self, value=1E-6):
	
        if isinstance(value, float):
            self._energy_ = value 
     
    @force.setter
    def force(self, value=None):
	
        if isinstance(value, float):
            self._force_ = value 
	
    @cutoff.setter
    def cutoff(self, value=1.3):
	
        if isinstance(value, (float,int)):
            self._cutoff_ = value 

    @nbands.setter
    def nbands(self, value=1.2):
	
        if isinstance(value, (float,int)):
            self._nbands_ = value 

class Tasks(VaspIncar):

    def __init__(self):
        self._xc_ = None
        self._tasks_ = None 
        self._accelerate_ = True
       
    @property
    def xc_func(self):
        return self._xc_

    @xc_func.setter
    def xc_func(self,value):

        if isinstance(value,str):
            gga = set()
            for key in value.lower().split('+'):

                # compute with default parameters %
                if key in ['pbe', 'pbesol','91','pe','rp','ps','am','pz','soc','gw','hse']:
                    if key == 'pbe': key = 'pe'
                    elif key == 'pbesol': key = 'ps'
                    gga.add(key)
            self.xc_update(gga)

        else:
            raise RuntimeError("Failed during set xc_func. Check your input !")

    def xc_update(self, value:list):

        if self._xc_ == None:
            self._xc_ = set()
        self._xc_.update(value)

        if isinstance(self._tasks_, Task):
            if 'xc' not in self._tasks_:
                self._tasks_['xc'] = []

            for i in ['soc','hse','gw']:
                if i in self._xc_ and i not in self._tasks_['xc']:
                    self._tasks_['xc'].append(i)
       	
    @property
    def tasks(self):
        return self._tasks_
	
    @tasks.setter
    def tasks(self,value):
        if isinstance(value,str):
            self._tasks_ = TaskBuilder.build(value)
        elif isinstance(value,(Task,dict)):
            self._tasks_ = value
        else:
            raise TypeError("Invaild tasks input. ")
        self.xc_update([])


    @property
    def accelerate(self):
        return self._accelerate_

    @accelerate.setter
    def accelerate(self,value):
        if isinstance(value, bool):
            self._accelerate_ = value
        elif isinstance(value, (dict,Incar)):
            self._accelerate_ = [Incar('accelerate',value)]
        elif isinstance(value,list):
            acc = []
            for v in value:
                if isinstance(v,dict):
                    acc.append(Incar('accelerate',v))
            if len(acc) != 0: 
                self._accelerate_ = acc
            else:
                self._accelerate_ = True
        else:
            raise ValueError('Invalid input for vasp.accelerate.')
