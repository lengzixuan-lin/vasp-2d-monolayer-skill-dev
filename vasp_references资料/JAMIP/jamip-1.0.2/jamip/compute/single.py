import os
from jamip.abtools.vasp.vaspflow import VaspFlow
from jamip.abtools.espresso.qeflow import QEFlow


class __QEFlow__(QEFlow):

    def __init__(self, qe, stdout=None, *args, **kwargs):

        import sys
        sys.path.insert(0,self.realpath)
        QEFlow.__init__(self,qe,stdout,*args,**kwargs)

class __VaspFlow__(VaspFlow):

    def __init__(self, vasp, stdout=None, *args, **kwargs):

        import sys
        sys.path.insert(0,self.realpath)
        VaspFlow.__init__(self,vasp,stdout,*args,**kwargs)

class SingleManager(object):

    def __init__(self,root=None):
        if root == None:
            self.root = os.path.abspath(root)
        else:
            self.root = os.getcwd()

    def submit(self,func,stdout):
        from .manager import TaskManager
        from .cluster import Cluster
        from os.path import dirname

        root = dirname(dirname(stdout))
        cluster = Cluster(root)
        taskdict = TaskManager(cluster.manager).get_task_by_user()
        if stdout in taskdict.values():
            print("Warning! A program is running in the current directory")
            return False

        self.write_log(stdout,'start')
        self.calculator(func,stdout)
        self.write_log(stdout,'end')
        return True

    def write_log(self,stdout,status):
        import time
        # tag the task status % 
        logfile = os.path.join(self.root,'single.log')
        with open(logfile,'a') as f:
            f.write('{0} {1} at {2}\n'.format(stdout,status,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

    @property
    def mpirun(self):
        return self.__command__

    @mpirun.setter
    def mpirun(self, command=None):
        if command is None:
            self.__command__ = self.default_command
        else:
            self.__command__ = command

    def calculator(self, func=None, stdout=None):

        from jamip.abtools.vasp.setvasp import SetVasp
        from jamip.abtools.espresso.setqe import SetQE

        if isinstance(func, SetVasp):
            __VaspFlow__(func, stdout)

        elif isinstance(func, SetQE):
            __QEFlow__(func, stdout)

        else:
            raise IOError ("only vasp and QE WorkFlow is valid ...")
