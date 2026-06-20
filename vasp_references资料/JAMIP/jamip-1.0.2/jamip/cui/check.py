from jamip.abtools.vasp.check import CheckStatus
from jamip.compute.pool import Pool
import os

class __CheckStatus(object):

    def __init__(self, params=None, *args, **kwargs):
        if 'pool' in params:
            self.poolname = os.path.abspath(params['pool']) 
            # show task status in form %
            if params['check']  == 'show':
                self.__form()

            if params['check']  == 'converge':
                self.__form_converge()

            # update poolfile base on .status %
            elif params['check']  == 'load':
                self.__load()

            # update .status %
            elif params['check'] == 'status':
                self.__status()

            elif params['check']  == 'prepare':
                self.__submit()

            if params['check']  in ['qstat','bjobs','squeue']:
                self.__qstat(params['check'],params['pool'])

        else:
            if params['check'] in ['qstat','bjobs','squeue']:
                self.__qstat(params['check'])
            else:
                raise ("Please add -f [poolname]")
        
    def __status(self):
        from ruamel import yaml
        pool = Pool().loader(self.poolname).pool
        success = 0
        
        for root,func in pool.items():
            cs = CheckStatus(root)
            file = os.path.join(root,'.status')
            status=cs.rebuild_status(func['functional'].tasks)
            with open(file, 'w') as f:
                yaml.dump(status, f, Dumper=yaml.RoundTripDumper, indent=3)
            success+=1
            if pool[root]['prior'] == 10 and len(status) > 0:
                pool[root]['prior'] = 9
        Pool().save(self.poolname,**pool)

        print('success: %s' %success)
                

    def __load(self):
        from jamip.abtools.base.tasks import Incar,Task
        pool = Pool().loader(self.poolname).pool
        
        num = 0
        for root,func in pool.items():
            status = Task('vasp')
            tasks = func['functional'].tasks
            for key in tasks:
                if isinstance(tasks[key],str):
                    status[key] = Incar(key)
                else:
                    for k in tasks[key]:
                        status[k] = Incar(k)
            CheckStatus._continue(status,root)
            job_status = 'finish'
            for key,task in status.items():
                if task.finish is not True:
                    job_status = 'wait'
                    break

            if pool[root]['status'] != job_status:
                pool[root]['status'] = job_status
                print("update pool:",root)
                num +=1

        Pool().save(self.poolname,**pool)
        print("Job-load finished. %d job changed." %num)

    def __submit(self):

        num = 0
        pool = Pool().loader(self.poolname).pool
        for i in pool.keys():
            if pool[i]['status'] == 'running':
                print('flush pool :',i)
                pool[i]['status'] = 'wait'
                pool[i]['prior'] = 10
                pool[i]['job_id'] = -1
                num += 1
        Pool().save(self.poolname,**pool)
        print("Job-prepare finished. %d job prepared." %num)

    def __qstat(self,order,jobid=None):
        from jamip.compute.manager import TaskManager
        
        cwd = os.path.realpath(os.getcwd())

        if order == 'qstat':
            tm = TaskManager('pbs') 

        elif order == 'bjobs':
            tm = TaskManager('lsf') 

        elif order == 'squeue':
            tm = TaskManager('slurm') 

        if jobid and jobid.isdigit():
            abspath = tm.get_task_by_id(jobid)
            if len(abspath) > 30 and abspath.startswith(cwd):
                print(jobid,':', abspath[len(cwd)+1:])
            else:
                print(jobid,':',abspath)

        else:
            job_dict = tm.get_task_by_user()
            if len(job_dict) != 0:
                for jobid,path in job_dict.items():
                    if len(path) > 30 and path.startswith(cwd):
                        print(jobid,':', path[len(cwd)+1:])
                    else:
                        print(jobid,':',path)
        
    def __form_converge(self):
        from collections import OrderedDict
        from jamip.utils.views import shellform

        # load pool %
        pool = Pool().loader(self.poolname).pool
        totallist = []
        for stdout,value in pool.items():
            data = OrderedDict.fromkeys(['path','last','step','dE','trend'],'--')
            data['path'] = stdout

            # get last relax path %
            status = CheckStatus.load_converge_status(stdout)
            if status == None: continue
            elif 'relax' in status and status['relax'].finish == False:
                print(status['relax'])
                data['last'] = status['relax'].path
                data['step'] = status['relax']['step']
                data['dE'] = status['relax']['dE']
                data['trend'] = status['relax']['trend']
                totallist.append(data)
            elif 'scf' in status and status['scf'].finish == False:
                data['last'] = status['scf'].path
                totallist.append(data)

        if len(totallist) > 0:
            shellform(totallist)
        else:
            print("All jobs converge.")

    def __form(self):
        from copy import deepcopy
        from collections import OrderedDict
        from jamip.utils.views import shellform 

        # load pool %
        pool = Pool().loader(self.poolname).pool
        totallist = []
        for root,func in pool.items():
            tmp = OrderedDict()
            for key in ['job_id','prior','status']:
                tmp[key] = func[key]

            if func['status'] in ['finish','running'] or func['prior'] < 10:
                status = CheckStatus.load_status(root)

                # create OrderedDict %
                tasks = func['functional'].tasks
                if 'relax' in tasks:
                    tmp['relax'] = '--'
                    if status.relax != None:
                        tmp['relax'] = status.relax.finish
             
                if 'scf' in tasks:
                    tmp['scf'] = '--'
                    if status.scf != None:
                        tmp['scf'] = status.scf.finish
             
                for key in tasks:
                    if key in ['relax','scf']: continue
                    for prop in tasks[key]:
                        tmp[prop] = '--'
                        if prop in status:
                            tmp[prop] =  status[prop].finish

            tmp['path'] = root
            totallist.append(tmp)

        shellform(totallist)
