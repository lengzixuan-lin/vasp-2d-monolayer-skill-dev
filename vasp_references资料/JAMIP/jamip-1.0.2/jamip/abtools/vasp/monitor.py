import threading
import psutil
import socket
import time
import os

def Writelog(path,text):
    import time
    with open('.history','a') as f:
        f.write('{0} monitor {1} at {2}\n'.format(path,text,time.strftime('%Y-%m-%d %H:%M:%S')))

class CPUcheck(object):

    @staticmethod
    def write_cluster_status(ncore=20,mode='w'):
        ncpu = psutil.cpu_count()
        pcpu = psutil.cpu_percent()
        pmem = psutil.virtual_memory().percent

        with open('cpu.txt',mode) as f:
            f.write('Record at %s \n' %time.strftime('%Y-%m-%d %H:%M:%S'))
            f.write('JOB run in %s\n' %socket.gethostname())
            # ncpu check %
            f.write('ncpu = %s\n' %ncpu)
            if ncpu != ncore:
                f.write("Warning! The actual CPU cores not match the set value!\n") 
            # pcpu check %
            f.write('pcpu = %s\n' %pcpu)
            if pcpu >  90:
                f.write("Warning! Excessive cpu usage\n") 
            # pmem check %
            f.write('pmem = %s\n' %pmem)
            if pmem >  90:
                f.write("Warning! Excessive memory usage\n") 
            # process check %
            vasppids = []
            for p in psutil.process_iter():
                if 'mpirun' in p.name():
                    f.write("Warning! mpirun job is running, job will exit\n")
                    try:
                        p.terminate()
                    except: 
                        f.write("kill mpirun failed.\n")
                elif 'vasp' in p.name():
                    if p.parent().pid == 1:
                        f.write('Warning! pid %s is an orphan vasp process.\n' %p.pid)
                    else:
                        vasppids.append(p.pid)

    @staticmethod
    def write_children_status(text=''):
        # clean all subprocess if exists! %
        p = psutil.Process(os.getpid())
        with open('cpu.txt','a') as f:
            #f.write('\nmain-pid : %s\n'%os.getpid())
            f.write('\n'+text+'\n')
            f.write('thread-num : %s\n'%p.num_threads())
            for i,sh in enumerate(p.children()):
                f.write('sh-%d : %s\n' %(i,sh.children()))


class log_debug(object):

    def __init__(self,stdout):
        self.root = stdout
        self.edict = self.get_errors()
        self.error = None
        self.pointer = 0

    def read_logs(self,login=None):
        from os.path import dirname,join
        if login is None:
            login = join(self.root,'pbs.log')
        with open(login,"r") as f:
            f.seek(self.pointer,0)
            lines = f.readlines()
            for line in lines:
                for key,value in self.edict.items():
                    if value in str(line):
                       self.error = key
                       break
            self.pointer = f.tell()

        # stop mpirun process if exists %
        if self.error is not None:
            p = psutil.Process(os.getpid())
            child = self.find_mpirun_process(p)
            if child is not None:
                child.terminate()

    def get_errors(self):
        from ruamel import yaml
        file = os.environ['HOME']+'/.jamip/env/error.yaml'
        Error = {}
        with open(file,'r') as f:
            errorset = yaml.safe_load(f)
        for key,value in errorset.items():
            Error[key] = value[0]
        return Error

    def find_mpirun_process(self,p):
        for sh in p.children():
            try:
                if len(sh.children()) == 0 :continue
                for child in sh.children():
                    if child.name() == 'mpirun':
                        return child
            except:
                pass 

class VASP_Thread(threading.Thread):

    def __init__(self,func,task,args=()):
        super(VASP_Thread,self).__init__()
        self.func = func
        self.task = task
        self.args = args

    def run(self):
        Writelog(self.task,'start')
        self.result = self.func(*self.args)
        Writelog(self.task,'end')

    def get_result(self):
        try:
            return self.result 
        except Exception:
            return None


def Monitor(func):
    def warp(self, vasp, stdout, stdin, incar={}, overwrite=True, **kwargs):
 
        # search running vasp %
        # CPUcheck.write_children_status('job start.')

        # run vasp thread %
        taskname = os.path.relpath(stdout,self.rootdir)
        monitor=VASP_Thread(func, taskname, args=[self,vasp, stdout, stdin, incar, overwrite])
        monitor.start()

        sleep = 0
        pointer = -1
        interval = 3
        vasplog = None
        p = psutil.Process(os.getpid())
        ld = log_debug(stdout)
        while threading.activeCount() > 1:

            # wait subprocess start %
            if vasplog is None:
                child = ld.find_mpirun_process(p)
                if child is not None:
                    vasplog = child.open_files()[0].path
                    with open(os.path.join(self.rootdir,'cpu.txt'),'a') as f:
                        f.write('\n%s task monitor\n' %taskname)
                        f.write("(pid='%s', name='%s', started='%s')\n" %(child.pid, child.name(), time.strftime('%Y-%m-%d %H:%M:%S')))
                        #f.write("log='%s'\n" %vasplog)

                if sleep > 20:
                    Writelog('Error!','exit for timeout')
                    break
                else:
                    sleep += 1
                    time.sleep(3)

            # read logs durning subprocess active%
            elif interval < 1000 :
                time.sleep(interval)
                ld.read_logs(vasplog)
                if pointer != ld.pointer:
                    pointer = ld.pointer
                else:
                    interval = interval*2
            else:
                break

                
        # finally read vasplog after subprocess finish %
        ld.read_logs(vasplog)
        if interval > 10000:
            CPUcheck.write_children_status('job overtime.')
            #with open("interval.log", 'a') as f:
            #    f.write('active=%d, interval=%d\n' %(threading.activeCount(), interval))

        # Analyze subprogress status after finish%
        monitor.join(60)
        if monitor.get_result() != None:
            stdout = monitor.get_result()
            Writelog(taskname,'join')
        else:
            os.chdir(self.rootdir)
            Writelog(taskname,'timeout')
            # kill mpirun %
            child = ld.find_mpirun_process(p)
            print(child)
            if child is not None:
                child.terminate()
            #with open("interval.log", 'a') as f:
            #    f.write('active=%d, interval=%d\n' %(threading.activeCount(), interval))

        # debug %
        if ld.error is not None and ("debug" not in kwargs or kwargs["debug"] != True):
            from .correcting import CorrectingFlow
            debugin,debug_incar = CorrectingFlow(self.rootdir).debug(ld.error, vasp, stdout, stdin, incar)
            vasp.tasks.debug = debug_incar
            Writelog(taskname,'debug finish')

            # move dictorys %
            debugout = os.path.join(self.rootdir,'debug',taskname.replace('/','_'))
            os.popen("mv {0} {1}".format(stdout,debugout)).readline() 
            os.popen("mv {0} {1}".format(debugin,stdout)).readline()

        return stdout
    return warp
