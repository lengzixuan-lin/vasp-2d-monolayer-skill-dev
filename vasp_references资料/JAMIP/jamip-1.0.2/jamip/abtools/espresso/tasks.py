from ..base.tasks import Incar, Task

'''
    @property
    def magnetic(self):
        if not hasattr(self,'__magnetic'):
            self.__magnetic == VaspIncar('magnetic',{'magmom':'1*1000'}) 
        return self.__magnetic

    def set_energy(self,energy):    
        try:
            self.default['etot_conv_thr'] = float(energy)
        except:
            pass

    def set_force(self,force):    
        try:
            self.default['forc_conv_thr'] = float(force) 
        except:
            pass
'''

class TaskBuilder(object):

    _xc_ = ['soc','hse','gw']
    _task_ = {'nscf':('dos','band','projwfc'),
              'optic':('optics','bse'),
              'phonon':('force','softmode','gruneisen')
             }

    def __init__(self, *args, **kwargs):

        self._data = None

    @property
    def diyflow(self):
        from jamip.abtools.diyflow import get_diy_modules
        return self._xc_

    @property
    def property(self):
        return self._task_

    @classmethod
    def build(cls,tasks):
        from jamip.abtools.diyflow import get_diy_modules
        data = Task('qe')
        # relax % 
        if 'vc-relax' in tasks:
            data['relax'] = 'isv'
        elif 'relax' in tasks:
            data['relax'] = 'i'
 
        # scf %
        if 'scf' in tasks:
            data['scf'] = ''

        # nonscf %
        for key,props in cls._task_.items():
            tmp = []
            for taskname in props:
                if taskname in tasks:
                    tmp.append(taskname)
            if len(tmp):
                data[key] = tmp

        # xc_func %
        tmp = []
        for key in cls._xc_:
            if key in tasks:
                tmp.append(key)
        if len(tmp):
            data['xc'] = xc

        # add diy-task if it exists in floder ~/abtools/diyflow
        tmp = []
        for module in get_diy_modules():
            if module in tasks:
                tmp.append(module)
        if len(tmp):
            data['diy'] = tmp
        
        return data
        
    @classmethod
    def create(cls,task,path):
        import os
        import warnings
        from os.path import dirname, join, relpath 
        from ruamel import yaml

        try:
            with open(join(path,'.incar')) as f:
                incarset = yaml.safe_load(f)
        except:
            raise IOError("Failed in read incar.yaml !")

        data = Task('qe',task)
        data._builder = cls
        # base % 
        if 'base' in incarset:
            data['base'] = Incar('base',incarset['base'])
        else:
            raise ValueError("Default parameters is necessary in incar !")

        # optimization % 
        if 'relax' in task and task['relax'] != None:
            if task['relax'] == 'i':
                params = {'calculation':'relax'}
            elif task['relax'] == 'isv':
                params = {'calculation':'vc-relax'}
            else:
                raise KeyError('Invalid relax parameters !')

            if 'relax' in incarset:
                params.update(incarset['relax'])
            data['relax'] = Incar('relax',params)
 
        # scf % 
        if 'scf' in task and task['scf'] != None:
            params = {}
            if 'scf' in incarset:
                params.update(incarset['scf'])
            data['scf'] = Incar('scf',params)

        # property %
        for key in cls._task_:
            params = {}
            if key in task and len(task[key]):
                for prop in task[key]:
                    if prop in incarset:
                        params[prop] = Incar(prop,incarset[prop])
                    else:
                        params[prop] = Incar(prop)
                data[key] = Task(key,params) 

        return data

    @classmethod
    def set_force(cls,task,force):
        task['base']['forc_conv_thr'] = float(force)

    @classmethod
    def set_energy(cls,task,energy):
        task['base']['etot_conv_thr'] = float(energy)


class QEIncar:

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

class Tasks(QEIncar):

    def __init__(self):
        self._xc_ = None
        self._tasks_ = None 
        self._accelerate_ = True
       
    @property
    def xc_func(self):
        return self._xc_

    @xc_func.setter
    def xc_func(self,value):
        if not isinstance(self.tasks,Task):
            self._xc_ = value

        elif isinstance(value,str) :
            gga = value.lower()
            # compute with default parameters %
            if gga in ['pbe', 'pbesol','91','pe','rp','ps','am']:
                if gga == 'pbe': gga = 'pe'
                elif gga == 'pbesol': gga = 'ps'

            # compute with extre parameters % 
            elif gga in ['soc','gw','hse']:
                 if 'xc' in self._tasks_:
                     self.tasks['xc'].append(gga)
                 else:
                     self.tasks['xc'] = [gga]
            self._xc_ = gga
        else:
            raise RuntimeError("Failed during set xc_func. Check your input !")

       	
    @property
    def tasks(self):
        return self._tasks_
	
    @tasks.setter
    def tasks(self,value):
        if isinstance(value,str):
            self._tasks_ = TaskBuilder().build(value)
        elif isinstance(value,(Task,dict)):
            self._tasks_ = value
        else:
            raise TypeError("Invaild tasks input. ")

        # add xc_func %
        if self._xc_ != None:
            self.xc_func = self._xc_

    @property
    def accelerate(self):
        return self._accelerate_

    @accelerate.setter
    def accelerate(self,value):
        if isinstance(value,bool):
            self._accelerate_ = value
        elif isinstance(value,(dict,QEparams)):
            self._accelerate_ = [QEparams('accelerate',value)]
        elif isinstance(value,list):
            acc = []
            for v in value:
                if isinstance(v,dict):
                    acc.append(QEparams('accelerate',v))
            if len(acc) != 0: 
                self._accelerate_ = acc
            else:
                self._accelerate_ = True
        else:
            raise ValueError('Invalid input for vasp.accelerate.')
