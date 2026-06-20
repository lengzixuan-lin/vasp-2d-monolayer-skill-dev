import os
from ..base.check import BaseStatus

class CheckStatus(BaseStatus):
    """
    cls to check the VASP
    """

    def __init__(self, rootdir, **kwargs):

        self.rootdir = rootdir
        self.threshold = 0.10
        self.converge = False
        self.constrain = False

    def success(self, path, task=None, **kwargs):
        """
        check vasp task run_status base on OUTCAR 
        """
        if os.path.exists(path):
            return self.get_status(path, task)
        else:
            return {'task':task,'success':False,'finish':False}

    @classmethod
    def _continue(cls, task, root, overwrite=False, **kwargs):
        from .tasks import TaskBuilder, Incar

        status = cls.load_status(root)

        # update task - opt&scf %
        if task.relax != None and task.relax.finish == False:
            if 'relax' in status and status.relax.finish:
                task.relax.finish = True

        if task.scf == None:
            if 'scf' in status and status.scf.finish:
                task.scf = Incar('scf',finish=True)
        elif task.scf.finish == False:
            if task.relax != None and task.relax.finish == False:
                task.scf.finish = False
            elif 'scf' in status and status.scf.finish:
                task.scf.finish = True

        if overwrite:
            remove_tasks = []

            for key in TaskBuilder().property:
                if key not in task: continue
                for prop in task[key]:
                    if prop in status:
                        remove_tasks.append(prop)
 
            # reset vasptask - diyflow %
            if 'diy' in task:
                for prop in task['diy']:
                    if prop in status:
                        remove_tasks.append(prop)

            cls(root).remove_status(remove_tasks)

        else:
            # reset vasptask - property %
            for key in TaskBuilder().property:
                if key not in task: continue
                for prop in task[key]:
                    if task[key][prop].finish == False:
                        if prop in status and status[prop].finish:
                            task[key][prop].finish = True
 
            # reset vasptask - diyflow %
            if 'diy' in task:
                for prop in TaskBuilder().diyflow:
                    if prop not in task['diy']: continue
                    if prop in status and status[prop].finish:
                        task['diy'][prop].finish = True

        # reset stdin %
        # get task stdin %
        if 'scf' in status and status.scf.finish:
            stdin = status.scf.path
        elif 'relax' in status:
            stdin = status.relax.path
            if not status.relax.finish:
                print('JOB continue from unfinish relax.')
        else:
            return None

        return os.path.join(root,stdin)

    def is_converge(self, path, conv=None):
        from jamip.analysis.vasp.outcar import GrepOutcar
        go = GrepOutcar()
        if conv == None:
            conv = go.ediff(path)
        oszicar = go.oszicar(path)
        if oszicar.size == 0 or oszicar[-1,-1] <= conv:
            return True

        return False
        
    def get_status(self, path=None, task=None):
        """	
        check chain: finish -> ion step -> electric step -> status
        """
        status = {'task':task, 'finish':False, 'success':False}
        
        try:
            return self.finish_check(status, path)
        except:
            print("OSError: Grep Information from pbs.log failed! ")
            print("Path: %s " %path)
            return status

    def finish_check(self, status, path):
        ''' step1 : finish '''
        
        # case 1 : normal calculation %
        line = os.popen("grep 'Total CPU time used (sec)' "+path).readline()
        if len(line) > 0:
            status['finish'] = True
            return self.ions_check(status, path)

        # case 2 : partchg or other nonscf calculation %
        line1 = os.popen("grep 'vasp will stop now' "+path).readline()
        line2 = os.popen("grep 'VASP will stop now' "+path).readline()
        if len(line1) > 0 or len(line2) >0 :
            status['finish'] = True
            status['success'] = True
            return status

        # case 3 : relax, to POSCAR and continue %
        logfile = os.path.join(os.path.dirname(path),'pbs.log')
        line = os.popen("grep 'to POSCAR and continue' "+logfile).readline()
        if len(line) > 0:
            status['finish'] = True
            return self.ions_check(status, path)

        return status

    def ions_check(self, status, path):
        ''' step2 : ions '''

        from jamip.analysis.vasp import GrepOutcar
        dir = os.path.dirname(path)
        go = GrepOutcar()

        # if allow ions relax %
        if go.nsw(dir) > 0:
            
            # energy converge or not %
            if go.ibrion(dir) in [1,2,3] and go.isif(dir) > 1:
                line = os.popen("grep 'reached required accuracy - stopping structural energy minimisation' "+path).readline() 
                if len(line) == 0:
                    status['ionic'] = False
                    return status
            status['ionic'] = True

            # force converged or not % 
            if self.constrain is True:
                status['force'] = go.max_force(dir)
                if status['force'] > self.threshold:
                    return status
                
        return self.electrons_check(status, path)
           
    def electrons_check(self, status, path):
        ''' step3 : electrons '''

        from jamip.analysis.vasp import GrepOutcar
        dir = os.path.dirname(path)
        go = GrepOutcar()

        # get last electronic step %
        line= os.popen("grep 'Iteration ' {0} | tail -1".format(path)).readline()
        electron_step = int(line.split('(')[-1].split(')')[0])

        if electron_step < go.nelm(dir):
            status['electronic'] = True
            status['success'] = True 
            return status
        else:
            status['electronic'] = False
            return status

    def rebuild_status(self,tasks):
        from os.path import exists,join
        from .tasks import Task
        import numpy as np
        if not isinstance(tasks,(Task,dict)):
            raise TypeError("Tasks should be Task class type")

        if exists(self.rootdir) and exists(join(self.rootdir,'pbsscript')):
            cwd = os.getcwd()
            os.chdir(self.rootdir)
        else:
            raise IOError('Invalid calculation path')

        status={}
        for task in tasks:
            if not exists(task): continue

            if task == 'relax':
                relaxs = os.listdir(task)
                if not len(relaxs): continue
                relax_end = join(task,max(relaxs))
                status[relax_end] = self.get_status(join(relax_end,'OUTCAR'), task) 

            elif task == 'scf':
                status[task] = self.get_status(join(task,'OUTCAR'),task) 

            else:
                for prop in tasks[task]:
                    path = join(task,prop)
                    if not exists(path): continue
                    if exists(join(path,'OUTCAR')):
                        status[path] = self.get_status(join(path,'OUTCAR'),prop) 

                    else:
                        subs = []
                        for sub in os.listdir(path):
                            if exists(join(path,sub,'OUTCAR')):
                                subs.append(self.success(join(path,sub,'OUTCAR'),prop)['success'])
                        if len(subs) > 0 and np.array(subs,dtype=bool).all():
                            status[path] = {'task':prop,'finish':True,'success':True}

        os.chdir(cwd)
        return status

    @classmethod
    def load_status(cls, root):
        ''' load finish status from .status '''

        from ..base.tasks import Incar, Task
        from os.path import join,exists
        from ruamel import yaml
        status = Task()

        if exists(join(root,'.status')):
            with open(join(root,'.status'),'r') as f:
                data = yaml.safe_load(f)
        else:
            return status

        if isinstance(data,dict):
            for path, value in data.items():
                task = value['task']
                if value['finish'] and task != None: 
                    status[task] = Incar(task, finish=value['success'], path=path) 

        return status

    @classmethod
    def load_converge_status(cls, root):
        ''' load converge status from .status '''

        from ..base.tasks import Incar, Task
        from jamip.analysis.vasp.outcar import GrepOutcar
        from scipy.optimize import curve_fit
        from os.path import join,exists
        from ruamel import yaml
        status = Task()

        if exists(join(root,'.status')):
            with open(join(root,'.status'),'r') as f:
                data = yaml.safe_load(f)
        else:
            return status

        history = []
        if isinstance(data,dict):
            for path, value in data.items():
                task = value['task']
                if value['finish'] and task != None: 
                    status[task] = Incar(task, finish=value['success'], path=path) 
                # relax finish %
                if path.startswith('relax'):
                    history.append(path)

        if 'relax' not in status:
            while len(history) > 0:
                path = history.pop()
                if data[path]['finish'] == True:
                    status['relax'] = Incar('relax', finish=data[path]['success'], path=path)
                    return status

        elif 'relax' in status:
            path = status['relax'].path
            if path == 'relax/S0':
                status['relax'].finish = False
                data[path]['success'] = False

            if data[path]['success'] != True:
                oszicar = GrepOutcar().oszicar(join(root,path))
                status['relax']['step'] = oszicar.shape[0]
                if oszicar.size > 1:
                    # dE in last step %
                    status['relax']['dE'] = '{:.2E}'.format(oszicar[-1][-1])
                    # Energy trend %
                    Y = oszicar[-10:,0]
                    X = range(len(Y))
                    mod = lambda x,a,b: a*x + b
                    try:
                        a,_ = curve_fit(mod,X,Y)[0]
                        if a < 0:
                            status['relax']['trend'] = 'down'
                        else:
                            status['relax']['trend'] = 'up'
                    except:
                        status['relax']['trend'] = '--'

        return status
