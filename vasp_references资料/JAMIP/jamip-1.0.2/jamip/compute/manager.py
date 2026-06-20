import os
from jamip.compute.launch import __LaunchTasks
from jamip.compute.cluster import Cluster
from jamip.compute.pool import Pool 

# step 0: open the jobs pool % 
# step 1: check current jobs and analysis % 
# step 2: update status of current jobs % 
# step 3: update resource % 
# step 4: load unfinished jobs % 
# step 5: submit jobs % 
class PBSManager:
    
    @classmethod
    def get_task_by_user(self,user):
        import re
        if user is None:
            user = os.environ['USER']
        lines = os.popen('qstat -u %s' %user).readlines()
        if len(lines) == 0 : return {}

        # normally 10th slice is run-status %
        for i,line in enumerate(lines):
            if re.match('Job',line):
                index = line.split().index('S')-1
                break

        # get self tasks %
        mytasks = []
        for line in lines[i:]:
            if re.match(r'\d+',line):
                if line.split()[index] != 'C':
                    mytasks.append(re.match(r'\d+',line).group())

        mtpath = {}
        for jobid in mytasks:
            mtpath[jobid] = self.get_task_by_id(jobid)

        return mtpath

    @classmethod
    def get_task_by_id(self,jobid=None):
        lines = os.popen('qstat -f '+jobid).readlines()
        path = ''
        for i,line in enumerate(lines):
            if 'PBS_O_WORKDIR=' in line:
                line = line.split('PBS_O_WORKDIR=')[-1]
                if ',' in line:
                    path = line.split(',')[0]
                if len(path) == 0:
                    path += line.rstrip()
                    for line in lines[i+1:]:
                        if line[0] != '\t': break
                        if ',' in line:
                            path += line.lstrip().split(',')[0]
                            break
                        else:
                            path += line.strip()

            if len(path) > 0:
                break

        return path

    @classmethod
    def get_host_by_id(self,jobid):
        import re
        lines = os.popen('qstat -f '+jobid).readlines()
        host = None
        for i,line in enumerate(lines):
            if 'exec_host' in line:
                hosts = re.findall('exec_host\s*=\s+([A-Za-z0-9-]+)',line)
                if len(hosts) > 0:
                    return hosts[0]
            elif 'PBS_O_HOST' in line:
                host = re.findall('PBS_O_HOST\s*=\s*([A-Za-z0-9-\.]+),',line)
                return host

        return host

class LSFManager:

    @classmethod
    def get_task_by_user(self,user):
        import re
        if user is None:
            user = os.environ['USER']
        lines = os.popen('bjobs -u %s' %user).readlines()
        if len(lines) < 2 : return {}

        # normally 3th slice is run-status %
        for i,line in enumerate(lines):
            if re.match('JOBID',line):
                index = line.split().index('STAT')
                break

        # get self tasks %
        mytasks = []
        for line in lines[i:]:
            if re.match(r'\d+',line):
                if line.split()[index] in ['RUN','PEND']:
                    mytasks.append(re.match(r'\d+',line).group())

        mtpath = {}
        for jobid in mytasks:
            mtpath[jobid] = self.get_task_by_id(jobid)

        return mtpath

    @classmethod
    def get_task_by_id(self,jobid=None):
        lines = os.popen('bjobs -l '+jobid).readlines()
        path = ''
        for i,line in enumerate(lines):
            if 'CWD <' in line:
                line = line.split('CWD <')[-1]
                if '>' in line:
                    path = line.split('>')[0]
                if len(path) == 0:
                    path += line.rstrip()
                    for line in lines[i+1:]:
                        if '>' in line:
                            path += line.split('>')[0].lstrip()
                            break
                        else:
                            path += line.strip()
            if len(path) > 0:
                break

        if path.startswith('$'):
            path = os.path.expandvars(path)
        return path

class SLURMManager:

    @classmethod
    def get_task_by_user(self,user):
        import re
        if user is None:
            user = os.environ['USER']
        lines = os.popen('squeue -u %s' %user).readlines()
        if len(lines) == 1 : return {}

        # normally 10th slice is run-status %
        for i,line in enumerate(lines):
            if re.match('JOBID',line.lstrip()):
                index = line.split().index('ST')
                break

        # get self tasks %
        mytasks = []
        for line in lines[i:]:
            if re.match(r'\d+',line.lstrip()):
                if line.split()[index] in ['R','PD']:
                    mytasks.append(re.match(r'\d+',line.lstrip()).group())

        mtpath = {}
        for jobid in mytasks:
            mtpath[jobid] = self.get_task_by_id(jobid)

        return mtpath

    @classmethod
    def get_task_by_id(self,jobid=None):
        lines = os.popen('scontrol show job '+jobid).readlines()
        path = ''
        for i,line in enumerate(lines):
            if 'WorkDir' in line:
                path = line.split('WorkDir=')[-1].rstrip()
                '''
                if '>' in line:
                    path = line.split('>')[0]
                if len(path) == 0:
                    path += line.rstrip()
                    for line in lines[i+1:]:
                        if '>' in line:
                            path += line.split('>')[0].lstrip()
                            break
                        else:
                            path += line.strip()
                '''
            if len(path) > 0:
                break

        return path

    @classmethod
    def get_host_by_id(self,jobid):
        import re
        lines = os.popen('scontrol show job '+jobid).readlines()
        host = None
        for i,line in enumerate(lines):
            if 'BatchHost' in line:
                line = line.split('BatchHost=')[-1].rstrip()
                break

        return host


class TaskManager(Pool):
    
    def __init__(self, manager='pbs',**kwargs):
        if manager.lower() == 'pbs':
            self.manager = PBSManager
        elif manager.lower() == 'lsf':
            self.manager = LSFManager
        elif manager.lower() == 'slurm':
            self.manager = SLURMManager
        self.manager.name = manager.lower()
         
    def get_task_by_user(self,user=None):
        return self.manager.get_task_by_user(user)

    def get_task_by_id(self,jobid=None):
        return self.manager.get_task_by_id(jobid)

    def get_host_by_id(self,jobid):
        return self.manager.get_host_by_id(jobid)

    def get_queue_num(self,username,root=None):
        taskdict = self.get_task_by_user(username)
        jamip_num = 0
        if len(taskdict) and root is not None:
            root = os.path.abspath(root)
            for jobid,path in taskdict.items():
                if path.startswith(root):
                    jamip_num += 1 
        return len(taskdict),jamip_num 

        
    def set_queue_num(self,username=None,root=None,type = 'mini'):
        cluster = Cluster(root)
        set_num = cluster.maximum
        user_num,jamip_num = self.get_queue_num(username,root)
        if type == 'prior':
            return set_num-jamip_num
        if type == 'mini':
            return max(set_num-user_num,1-jamip_num)


    def getfunc(self,poolfile,key):
        from time import sleep
        if not os.path.exists(poolfile):
            raise IOError ("Pool are moved or deleted. Please check %s" %poolfile)
        pool = self.loader(poolfile)
        self.__release__()
        if pool != None:
            return self.pool[key]['functional']
        else:
            raise IOError ("Pool is busy, try to reduce the task pool size")


    def calculator(self, func=None, stdout=None):

        from jamip.abtools.vasp.setvasp import SetVasp
        from jamip.abtools.vasp.vaspflow import VaspFlow
        from jamip.abtools.espresso.setqe import SetQE
        from jamip.abtools.espresso.qeflow import QEFlow

        if isinstance(func, SetVasp):
            VaspFlow(func, stdout)
        elif isinstance(func, SetQE):
            QEFlow(func, stdout)
        else:
            raise IOError ("only VASP and QE WorkFlow is valid ...")	


def main(stdout,pool,ignore=False):
    root  = os.path.dirname(pool) 

    # load overwrite/restart %
    cluster = Cluster(root)
    username = cluster.user

    task=TaskManager(cluster.manager)
    task_num = 0 
    for path in task.get_task_by_user(username).values():
        if path == os.getcwd():
            task_num += 1
    if task_num >1 and not ignore:
        print("Warning! A program is running in the current directory\nTask stop.")
    else:
        func=task.getfunc(pool,stdout)
 
        if cluster.overwrite and not ignore:
            func.overwrite = True

        # tag the status % 
        if os.path.exists('.wait'):
            os.system('rm .wait')
 
        # start calculation %
        task.calculator(func,os.getcwd())
 
        # save data % 
        #if getattr(func,'save',False) or getattr(func,'savedb',False):
        #    a = __Analysis(pool,stdout)

    # next calculation %
    os.chdir(root)
    new_task_number = task.set_queue_num(username,root,type='prior') + 1
    newjob = {'run':'qsub','pool':pool,'maximum':new_task_number,\
              'restart':cluster.restart,'overwrite':cluster.overwrite}
    __LaunchTasks(newjob,*[stdout])

# main program % 
if __name__ == '__main__':
    import sys

    stdout = sys.argv[2]
    pool   = sys.argv[1] 
    main(stdout,pool)
