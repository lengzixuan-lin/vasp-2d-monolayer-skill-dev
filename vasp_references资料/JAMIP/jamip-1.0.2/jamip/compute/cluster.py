import os
from collections import UserDict

class Cluster(UserDict):

    _project = 'JUMP2.pbs'
    script = 'pbsscript'
    maximum = 10

    def __init__(self,root=None, params=None, **kwargs):

        if root != None:
            self.__load__(root)
        if params != None:
            self.data.update(params)

    def __load__(self, root, file='.cluster'):
        '''
        load cluster configuration
        params:
            root: job submission path
            file: filename of config file
            params: update config params
        '''
        from os.path import exists, join
        from ruamel import yaml

        # load configuration file% 
        if root != None and exists(join(root,file)):
            with open(join(root,'.cluster'),'r') as f:
                self.data = yaml.safe_load(f)
        else:
            msg = "Cluster config file %s not exists!" %file
            raise IOError(msg)

    def __dump__(self, root, params=None, file='.cluster'):
        from copy import deepcopy
        from ruamel import yaml

        dat = deepcopy(self.data)
        if params != None: 
            dat.update(params)
        with open(os.path.join(root,'.cluster'),'w') as f:
            yaml.dump(dat, f, Dumper=yaml.RoundTripDumper,indent=3)

    def submit(self, pool, outdir, **params):
	
        self.write_script(pool, outdir) 
        command = '{0} {1} | tail -1'.format(self.cmd,self.script)
        self.index = os.popen(command).readline()

    @property
    def index(self):
        return self.__id 

    @index.setter
    def index(self, value=None):
        import re
        self.__id = re.findall(r'\d+', value)[:1]
    
    def write_script(self, pool, outdir, program='compute/manager.py'):

        from os.path import dirname,join,exists 
        import jamip

        script = join(dirname(jamip.__file__), program)
        if not exists(script):
            raise IOError('Submit program %s not exists !' %script)

        output = '.running'
        if program != 'compute/manager.py':
            output = '.output'

        with open(self.script, 'w') as f:
            if self.data['manager'] == 'PBS':	
                f.write('#!{0} \n'.format(os.environ['SHELL']))
                f.write('#PBS -N {0}\n'.format(self.project))
                f.write('#PBS -q {0}\n'.format(self.data['queue']))
                f.write('#PBS -l nodes={0}:ppn={1}\n'.format(self.data['nodes'],self.data['cores']))
                if 'feature' in self.data:
                    f.write('#PBS -l feature={0}\n'.format(self.data['feature']))
                if 'walltime' in self.data:
                    f.write('#PBS -l walltime={0}\n'.format(self.data['walltime']))
                f.write('#PBS -e .error\n')
                f.write('#PBS -o .output\n')
                f.write('\ncd $PBS_O_WORKDIR\n')	

            elif self.data['manager'] == 'LSF':	
                f.write('#!{0} \n'.format(os.environ['SHELL']))
                f.write('#BSUB -J {0}\n'.format(self.project))
                f.write('#BSUB -q {0}\n'.format(self.data['queue']))
                if 'app' in self.data:
                    f.write('#BSUB -app {0}\n'.format(self.data['app']))
                if 'lsfmpi' in self.data:
                    f.write('#BSUB -a {0}\n'.format(self.data['lsfmpi']))
                    f.write('#BSUB -R "span[ptile={0}]" -R "cu[usablecuslots={0}]"\n'.format(self.data['cores']))
                f.write('#BSUB -n {0}\n'.format(self.data['nodes']*self.data['cores']))
                f.write('#BSUB -e .error\n')
                f.write('#BSUB -o .output\n')
                f.write('\n')

            elif self.data['manager'] == 'SLURM':	
                f.write('#!{0}\n'.format(os.environ['SHELL']))
                f.write('#SBATCH -J {0}\n'.format(self.project))
                f.write('#SBATCH -p {0}\n'.format(self.data['queue']))
                f.write('#SBATCH -N {0}\n'.format(self.data['nodes']))
                if 'ntasks' in self.data:
                    f.write('#SBATCH -n {0}\n'.format(self.data['ntasks']))
                if 'cpus-per-task' in self.data:
                    f.write('#SBATCH -c {0}\n'.format(self.data['cpus-per-task']))
                if 'time' in self.data:
                    f.write('#SBATCH -t {0}\n'.format(self.data['time']))
                # if 'gpu' in self.data:
                #      f.write("#SBATCH --gres=gpu:{0}\n".format(self.data['gpu']))
                # if self.account is not None:
                #     f.write('#SBATCH -A {0}\n'.format(self.account))
                f.write('#SBATCH -e .error\n')
                f.write('#SBATCH -o .output\n')
                f.write('\n')
                

            # Common content: Environment and submit comment %
            if 'env' in self.data:
                if isinstance(self.data['env'],list): 
                    for line in self.data['env']:
                        f.write(line+'\n')
                elif isinstance(self.data['env'],str):
                    f.write(self.data['env']+'\n')
                     
                f.write('\n')

            command = 'python3 {0} {1} {2} > {3}\n'.format(script, pool, outdir, output)
            f.write(command)


    @property
    def manager(self):
        return self.data['manager']
    @property
    def mpi(self):
        return self.data['mpi']   
    @property
    def cores(self):
        if self.manager.lower() == 'slurm':
            return self.data['ntasks']
        else:
            return self.data['cores']
    @property
    def cmd(self):
        return self.data['cmd']  
    @property
    def run(self):
        if self.data['mpi'] == 'mpirun':
            if self.manager.lower() in ['pbs','lsf']:
                return '{0} -np {1}'.format(self.data['mpi'],self.data['cores']*self.data['nodes'])
            elif self.manager.lower() == 'slurm':
                return '{0} -np {1}'.format(self.data['mpi'],self.data['ntasks'])
        else:
            return self.data['mpi']

    @property
    def user(self):
        if 'user' in self.data:
            return self.data['user']
        else:
            return os.environ['USER']
    @property
    def restart(self):
        if 'restart' in self.data:
            return self.data['restart'] 
        else:
            return False
    @property
    def overwrite(self):
        if 'overwrite' in self.data:
            return self.data['overwrite'] 
        else:
            return False
    @property
    def maximum(self):
        if 'maximum' in self.data:
            return self.data['maximum'] 
        else:
            return self.maximum
    @property
    def project(self):
        if 'project' in self.data:
            return self.data['project']
        else:
            return self._project 
       
