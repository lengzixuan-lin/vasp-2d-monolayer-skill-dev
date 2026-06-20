# prepare
from os.path import exists,join
from ruamel import yaml
import os

class Prepare(object):
    
    env = '{0}/.jamip/env'.format(os.environ['HOME'])

    @classmethod
    def pool(cls,func):
        return pool_prepare(func)

    @classmethod
    def cluster(cls,system='pbs'):
        import shutil
        system = system.lower()
        if exists('.cluster'): 
            try:
                with open('.cluster','r') as f:
                    params = yaml.safe_load(f)

                if params["manager"].lower() != system:
                    backup = '.'+params["manager"].lower()
                    os.rename('.cluster',backup)
                    print("warning! cluster manager changed! The original file is backed up to %s" %backup)
                elif 'restart' in params and params["restart"] == True: 
                    print("Warning! 'restart' is set in .cluster! Make sure it is correct.")
                elif 'overwrite' in params and params["overwrite"] == True: 
                    print("Warning! 'overwrite' is set in .cluster! Make sure it is correct.")

            except Exception as e:
                cls.yaml_error('.cluster',e)

        if not exists('.cluster'): 
            try:
                shutil.copy(join(cls.env,system+'.yaml'),'.cluster')
            except:
                raise IOError ("%s.yaml not exist! in ~/.jamip/env/" %system)

    @classmethod
    def incar(cls,tasks,default=None):

        if default == None:
            default = cls.env+os.sep+tasks.soft+'.yaml'

        # load default_incar %
        if exists(default):
            try:
                with open(default,'r') as f:
                    default_incar = yaml.safe_load(f)
            except Exception as e:
                cls.yaml_error(default,e)
        else:
            raise IOError("incar.yaml not exists in ~/.jamip/env/")

        # load incar in local path %
        current_incar = {}
        if exists('.incar'):
            try:
                with open('.incar','r') as f:
                    current_incar = yaml.safe_load(f)
            except Exception as e:
                cls.yaml_error(default,e)

        # build incar.yaml %
        # base_task = ['base','scf','band']
        queue = ['base', 'relax', 'scf']
        for key in tasks.keys():
            if key == 'md':
                queue.append(tasks[key])

            elif isinstance(tasks[key],list):
                if key == 'diy': continue
                queue.extend(tasks[key])

        # add task for want probably %
        if 'electric' in tasks:
            queue.append('band') 

        # build diy_input %
        if 'diy' in tasks:
            diy_dict = {}
            from jamip.abtools.diyflow import import_diy_module
            for task in tasks['diy']:
                if task not in current_incar: 
                    diy_class = import_diy_module(task)
                    current_incar[task] = diy_class.yaml

        for task in queue:
            if task not in current_incar: 
                if task in default_incar:
                    current_incar[task] = default_incar[task]
                else:
                    print('missing {} parameter in default_incar. '.format(task))
                    current_incar[task] = {}

        with open('.incar','w') as f:
            yaml.dump(current_incar, f, Dumper=yaml.RoundTripDumper,indent=3)


    @classmethod            
    def yaml_error(cls,file,error):
        print("Syntax error in %s" %file)
        print('  ',repr(e))
        os.sys.exit()
         
    @classmethod
    def checkdb(cls,db='mysqld'):
        user = os.environ['USER']
        dbrun = True
        # database check %
        lines = os.popen("ps -ef|grep %s" %db).readlines()
        for line in lines:
            if line.startswith(user) and line.split()[2] == '1':
                dbrun = False
        if dbrun:
            print("Database %s is not running" %db)

class pool_prepare(object):


    def __init__(self,func):
        super(pool_prepare,self).__init__()
        self.func = func

    def set_structure(self,poolpath,calpath='./CAL',operation = None,prior = None):
        from .pool import Pool
        from copy import deepcopy
        from jamip.structure import read

        pool = Pool()
        # tasks class to dict %
        task = self.func.tasks
        self.func.tasks = task.data
        if isinstance(prior,int):
            pool.prior = prior
        for i in os.walk(poolpath).__next__()[2]:
            pool.functional = deepcopy(self.func)
            poscar = read(poolpath+'/'+i)
            if operation:
                poscar = operation(poscar)
            pool.functional.structure = poscar
            pool.outdir = calpath.rstrip('/') + '/' + i
        self.pool = pool
        self.func.tasks = task

    def set_extra(self,type='colinear'):
        '''
        create magmom configuration file with default format
        type:
            cl : colinear, need to set magmom for each atom
            ncl: non-colinear, need to set all three directions of magmom 
        '''
        if self.func.tasks.xc != None and 'soc' in self.func.tasks.xc:
            type = 'non-colinear'

        params = {}
        if exists('.extra'):
            try:
                with open('.extra','r') as f:
                    data = yaml.safe_load(f)
                    if data != None:
                        params = data
            except Exception as e:
                Prepare.yaml_error('.extra',e)

        with open('.extra','w') as f:
            f.write('# %s magnetic moment\n' %type)
            for key,format in self.pool.mainkey.items():
                f.write('%s : # %s\n' %(key,format))
                f.write('   magmom : ')
                if key in params and 'magmom' in params[key] and params[key]['magmom'] != None:
                    f.write(params[key]['magmom'])
                f.write('\n')

    def save(self,name ='JUMP2.pbs',overwrite ='True'):
        self.pool.save(name,overwrite)    
 
