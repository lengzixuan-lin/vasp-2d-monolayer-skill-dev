from jamip.abtools.vasp.vaspflow import VaspFlow

class Baseflow(VaspFlow):

    def __init__(self, func=None, stdout=None, *args, **kwargs):

        from os.path import dirname,abspath,relpath
        from jamip.compute.cluster import Cluster

        # stdout directoty %
        if stdout:
            self.rootdir = abspath(stdout)
        else:
            self.rootdir = abspath(os.getcwd())

        # initialize cluster params %
        submit_path = dirname(dirname(self.rootdir))
        path = relpath(self.rootdir,submit_path)
        self.cluster = Cluster(submit_path)

    def exit(self,func):
        for key in func.tasks:
            if func.tasks[key] != None:
                func.tasks[key].finish = True





