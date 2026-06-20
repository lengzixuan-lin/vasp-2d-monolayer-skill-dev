import os
from ..base.check import BaseStatus

class CheckStatus(BaseStatus):
    """
    cls to check the QE
    """

    def __init__(self, rootdir, *args, **kwargs):

        self.rootdir = rootdir
        self.rundir = rootdir+'/qerun'

    def success(self, stdout, task=None, **kwargs):
        """
        check espresso task run_status base on task.out
        """
        # file check %
        from os.path import join,exists
        import shutil

        outfile = join(self.rundir,task+'.out')
        if exists(outfile):
            status = self.get_status(outfile, task)
            xmlfile = stdout+'.xml'
            if exists(xmlfile):
                shutil.copy(xmlfile,self.rundir)
                os.remove(xmlfile)
        else:
            status = {'task':task,'finish':False,'success':False}

        return status

    @classmethod
    def _continue(cls, task, root, overwrite=False, **kwargs):
        from .tasks import TaskBuilder

        status = cls.load_status(root)

        # reset vasptask - opt&scf %
        if task.relax != None and task.relax.finish == False:
            if 'relax' in status and status.relax.finish: 
                task.relax.finish = True

        if task.scf != None and task.scf.finish == False:
            if 'scf' in status and status.scf.finish:
                task.scf.finish = True

        # reset vasptask - nonscf %
        if not overwrite:
            for key in TaskBuilder().property:
                if key not in task: continue
                for prop in task[key]:
                    if task[key][prop].finish == False:
                        if prop in status and status[prop].finish:
                            task[key][prop].finish = True

        # reset stdin %
        if 'scf' in status and status.scf.finish:
            stdin = status.scf.path
        elif 'relax' in status and status.relax.finish:
            stdin = status.relax.path
        else:
            return None

        return os.path.join(root,stdin)

    def get_status(self, path, task=None):
        """     
        check chain: finish -> ion step -> electric step -> status
        """
        status = {'task':task, 'finish':False, 'success':False}

        try:
            return self.finish_check(status, path)
        except:
            print("OSError: Grep Information from %s failed! " %path)
            print("Path: %s " %path)
            return status
            
    def finish_check(self, status, path):
        ''' step1 : finish '''

        line = os.popen("grep 'JOB DONE' "+path).readline()
        if len(line) > 0:
            status['finish'] = True
            status['success'] = True 

        return status

    def rebuild_status(self,root,tasks):
        """
        rebuild .status base on calculation files. 
        """
        raise 

    @classmethod
    def load_status(cls,root):
        from ..base.tasks import Incar, Task
        from os.path import join,exists
        from ruamel import yaml
        import numpy as np
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
                    status[task] = Incar(task, finish=value['finish'], path=path)

        return status
