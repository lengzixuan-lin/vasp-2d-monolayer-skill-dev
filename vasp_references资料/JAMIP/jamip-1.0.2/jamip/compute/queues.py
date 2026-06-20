import os
import heapq
import socket
from ruamel import yaml

class PriorityQueue:

    def __init__(self):
        self._index = 0
        self.queue = []

    def push(self, priority, val):
        heapq.heappush(self.queue, (priority, self._index, val))
        self._index += 1

    def pop(self):
        return heapq.heappop(self.queue)[-1]

    @property
    def empty(self):
        return len(self.queue) == 0

class Task:
    def __init__(self, stdout, builder, priority=1, **kwargs):
        import uuid
        self._id = uuid.uuid4().hex
        self.stdout = stdout
        self.builder = builder
        self.priority = priority
        self.kwargs = kwargs
        self._outputs = None

    @property
    def id(self):
        return self._id

    @property
    def outputs(self):
        return self._outputs

    @outputs.setter
    def outputs(self, value):
        self._outputs = value

    def run(self):
        
        try:
            cmd = "{mpi} {program} > pbs.log".format(mpi=self.builder.cluster.run, 
                                                     program=self.builder.program)
        except:
            raise AttributeError("VaspFlow.cluster object has no attribute 'mpi' or 'cores'")

        os.popen(cmd).readline()
        return self.stdout

    def check(self,stdout):
        if self.builder.soft == 'vasp':
            from jamip.abtools.vasp.check import CheckStatus
        elif self.builder.soft == 'qe':
            from jamip.abtools.espresso.check import CheckStatus

        check = CheckStatus(self.stdout)
        status = check.success(os.path.join(stdout,'OUTCAR'))
        return {'path': stdout,
                'status': status['finish'],
                'success': status['success']}

    @staticmethod
    def check_all(data):
        import numpy as np
        import re

        config = data.pop('configuration')
        if config['soft'] == 'vasp':
            from jamip.abtools.vasp.check import CheckStatus
        elif config['soft'] == 'qe':
            from jamip.abtools.espresso.check import CheckStatus

        total = []
        check = CheckStatus(config['rootdir'])
        for path,params in data.items():
            total.append(params['success'])
        if len(total) > 0 and np.array(total,dtype=bool).all():
            status={'task':config['task'],
                    'finish':True,
                    'success':True}
            key = re.findall('[A-Za-z]*/gruneisen/',path)
            path = key[0] if len(key) else os.path.dirname(path)
            check.write_status(status, path)
            return True
        else:
            return False


class TaskQueue:
    
    def __init__(self,source_file:str):
        from jamip.compute.cluster import Cluster
        from os.path import exists, dirname

        self.source = source_file
        self._results = {}

        if not os.path.exists(source_file):
            raise OSError('File %s not exists.' %source_file)

        with open(source_file,'r+') as f:
            data = yaml.safe_load(f)
            if 'configuration' in data :
                params = data['configuration'] 
            else:
                raise OSError('Failed load configuration from poolfile!')

        self.soft = params['soft']
        self.task = params['task']
        self.pool = params['pool']
        self.manager = params['manager']
        self.program = params['program']
        self.rootdir = params['rootdir']  
        self.cluster = Cluster(dirname(dirname(self.rootdir)))

    def run(self,task=None):
        # initialize %
        if task == None:
            task = self.puts(self.load())
        # run job %
        if task != None:
            self.callback(self.mpirun(task))
        else:
            with open('.history','a') as f:
                f.write("Job on %s Finished!\n" %socket.gethostname())
            self.finish()

    def finish(self):
        from jamip.compute.manager import TaskManager,main
        from os.path import dirname,relpath
        import fcntl
        # load status %
        data = self.load()
        fcntl.flock(self.source,fcntl.LOCK_UN)
        self.source.close()

        # check status %
        status = Task.check_all(data)
        
        manager = TaskManager(self.manager)
        task_num = 0
        jobs = []
        for jobid,path in manager.get_task_by_user(os.environ['USER']).items():
            if path == os.getcwd():
                task_num += 1
                jobs.append(jobid)

        # start mainflow if job end%
        if task_num == 1 or status:
            pool = self.pool
            stdout = relpath(self.rootdir,dirname(pool))
            main(stdout, pool, True)

    def callback(self,status):
        data = self.load()
        stdout = status.pop('path')
        data[stdout].update(status)
        self.run(self.puts(data))

    def puts(self,data):
        import fcntl
        for path, params in data.items():
            if path == 'configuration': continue
            if params['priority'] < 3:
                if params['status'] == 'wait':
                    self.put(Task(path, self, **params))
                elif params['status'] == 'running' and params['host'] == socket.gethostname():
                    self.put(Task(path,**params))

        task = None
        if not self.queue.empty:
            task = self.get()
            data[task.stdout]['host'] = socket.gethostname()
            data[task.stdout]['status'] = 'running'
            data[task.stdout]['priority'] += 1

        # rewrite and close file %
        self.source.seek(0)
        self.source.truncate()
        yaml.dump(data, self.source, Dumper=yaml.RoundTripDumper)
        fcntl.flock(self.source,fcntl.LOCK_UN)
        self.source.close()
        self.source = self.source.name

        return task

    def load(self):
        import fcntl
        if not isinstance(self.source,str):
            raise RuntimeError('File type Error.')

        elif not os.path.exists(self.source):
            raise OSError('File %s not exists. ' %self.source)

        self.queue = PriorityQueue()
        self.source = open(self.source,'r+') 
        fcntl.flock(self.source,fcntl.LOCK_EX)
        data = yaml.safe_load(self.source)
        return data

    def put(self, task: Task):
        self.queue.push(task.priority, task)
        return task.id

    def get(self):
        return self.queue.pop()

    def mpirun(self,task):
        os.chdir(task.stdout)
        stdout = task.run()
        os.chdir(self.rootdir)
        print('task %s finish' %task.stdout)
        return task.check(stdout)

    def get_output(self,task_id: str):
        return self.r.get(task_id, None)

    def get_result(self,task_id: str):
        return self._results.get(task_id, None)
           

if __name__ == '__main__':
    import sys
    pool   = sys.argv[1] 
    root   = sys.argv[2] 
    print(root)

    # load overwrite/restart %
    os.chdir(root)
    task_queue = TaskQueue(pool)
    task_queue.run()

