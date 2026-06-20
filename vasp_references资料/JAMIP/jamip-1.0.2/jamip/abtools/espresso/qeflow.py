#from .monitor import Monitor
from .check import CheckStatus
import os

class QEFlow(object):

    def __init__(self, func, stdout=None, *args, **kwargs):

        from .tasks import TaskBuilder
        from .setqe import SetQE
        from os.path import dirname,abspath,join,exists
        from jamip.compute.cluster import Cluster

        # stdout directoty %
        if stdout:
            self.rootdir = abspath(stdout)
        else:
            self.rootdir = abspath(os.getcwd())
        self.rundir = join(self.rootdir,'qerun')
        self.savedir = join(self.rootdir,'qesave')
        if not exists(self.rundir):
            os.makedirs(self.rundir)

        # initialize cluster params %
        submit_path = dirname(dirname(self.rootdir))
        self.cluster = Cluster(submit_path)
        # classify the tasks % 	
        if isinstance(func, SetQE):
            func.tasks = TaskBuilder.create(func.tasks,submit_path)
            func.tasks.set_energy(func.energy)
            func.tasks.set_force(func.force)
        else:
            raise TypeError('Invalid func. Make sure you input a SetVasp class!')

        self.qe_calculator(func, stdout) 
	
    def qe_calculator(self, qe, stdout, stdin=None, **kwargs):
        
        from copy import deepcopy
        from os.path import exists, join, abspath 
        from .check import CheckStatus
        from .tasks import TaskBuilder
	
        #CPUcheck.write_cluster_status(self.cluster.cores)

        if exists(stdout) and exists(join(stdout,'.status')):
            stdin = CheckStatus._continue(qe.tasks, stdout)

        print('Job start from :', stdin)
        # optimization % 
        if qe.tasks.relax is not None and qe.tasks.relax.finish is False:
            stdin = self.relax_cell_ions(qe, stdin)

            # exit calculation-flow if task error % 
            if qe.tasks.relax.finish == False:
                print("Warning! relax calculation is not converged.")
                self.exit(qe)

        # single point calculation %
        if qe.tasks.scf is not None and qe.tasks.scf.finish is False:
            stdin = self.single_point(qe, stdin)

            # exit calculation-flow if task error % 
            if qe.tasks.scf.finish == False:
                print("Scf calculation exit for relax calculation is not converged.")
                self.exit(qe)

        # properties calculation %
        for key in TaskBuilder().property:
            if key in qe.tasks and qe.tasks[key].finish is False:
                for prop in qe.tasks[key]:
                    if qe.tasks[key][prop].finish is False:
                        self.calc_property(key, qe, prop, stdin)
		
        print('Calculation finished')


    def calc_property(self, case, qe, prop, stdin):
        if case == 'nscf':
            self.nscf_property(qe, prop, stdin)
        elif case == 'optic':
            self.optic_property(qe, prop, stdin)
        elif case == 'phonon':
            self.phonon_property(qe, prop, stdin) 
        elif case == 'mechanic':
            self.mechanic_property(qe, prop, stdin)
  
    def plotter(self, qe, incar=None, **kwargs):

        from os.path import relpath,join,exists

        incar['outdir'] = relpath(self.savedir,self.rundir)
        os.chdir(self.rundir)

        # run qe progam % 
        program = incar.name+'.x'
        # try absolute path %
        if exists(join(qe.program,program)):
            program = join(qe.program,program)
        filename = qe.write_plot(incar)
        self.run(program, incar.name+'.plt')

        return True 

    #@Monitor
    def calculator(self, qe, stdin=None, incar=None,**kwargs):

        from jamip.structure import read 
        from os.path import join, exists, relpath 
        import shutil

        task = incar['prefix']
        calc = incar['calculation']
        stdout = join(self.savedir,task)

        # copy wfc and chg %
        if calc in ['vc-relax','relax','scf']:
            program = 'pw.x'

        elif calc in ['nscf','bands','md','vc-md']:
            if exists(stdout+'.save'):
                shutil.rmtree(stdout+'.save')

            if stdin != None and exists(stdin+'.save'):
                shutil.copytree(stdin+'.save',stdout+'.save')
            program = 'pw.x'

        elif calc in ['phonon']:
            program = 'ph.x'

        else:
            raise KeyError("Unsupport calc type %s." %calc)

        # try absolute path %
        if exists(join(qe.program,program)):
            program = join(qe.program,program)
        incar['outdir'] = relpath(self.savedir,self.rundir)
        os.chdir(self.rundir)
            
        incar = qe.set_input(qe.structure, incar)

        # run qe progam % 
        self.run(program, task)

        return stdout 

    # run % 
    def run(self, program, task):
 
        try:
            cmd = "{mpi} {program} < {task}.in > {task}.out ".format(mpi=self.cluster.run,program=program,task=task)
        except:   
            raise AttributeError("QEFlow.cluster object has no attribute 'mpi' or 'cores'")
        os.popen(cmd).readline()
 
    def single_point(self, qe, stdin=None, **kwargs):
	
        from os.path import join

        # task start %
        params = qe.tasks.scf
        params['calculation'] = 'scf'
        params["prefix"] = 'scf'
        stdout = self.calculator(qe, stdin, incar=qe.tasks.scf)
        qe.tasks.scf.finish = True

        # check status % 	
        check = CheckStatus(self.rootdir)
        status = check.success(stdout,task='scf')
        check.write_status(status, stdout)

        return stdout
	
    def relax_cell_ions(self, qe, stdin=None, steps=3, **kwargs):
        """
        function to relax the cell shape, internal inons and volume.
        """
        from os.path import join  

        check = CheckStatus(self.rootdir)
        params = qe.tasks.relax
        params['prefix'] = 'relax' 
        # run qe object % 
        stdout = self.calculator(qe, stdin, incar=params)
        qe.tasks.relax.finish = True

        # check status %
        status = check.success(stdout,task='relax')
        check.write_status(status, stdout)

        return stdout
  
    def nscf_property(self, qe, case, stdin, **kwargs):

        """
        select the case of tasks
        """
        from jamip.analysis.qe import BandFinder
        from os.path import join, exists, dirname
        from ..base.tasks import Incar
        from copy import deepcopy
        import numpy as np
        import shutil

        # get incar params%
        params = qe.tasks.nscf[case]
        check = CheckStatus(self.rootdir)
        total = []

        if case == 'band':
            # get kpath - input.py or automatic generation % 
            if 'band' in qe.kpath:
                band = qe.kpath['band'].kpoints

            else:
                band = self.get_band_kpath(qe.structure)

            # get nbands %
            params['calculation'] = 'bands'
            params['prefix'] = case
            if 'nbnd' not in params:
                params['nbnd'] = self._get_nband(qe,stdin)

            bandqe = deepcopy(qe)
            # loop the kpoints % 
            bandqe.kpoints = band
            stdout = self.calculator(bandqe, stdin, incar=params)
            status = check.success(stdout,case)
            check.write_status(status, stdout)
 
        elif case == 'dos' or case == 'projwfc':
            params['calculation'] = 'nscf'
            params['prefix'] = case
            nscfqe = deepcopy(qe)
            # step 1 : nscf calculation %
            stdout = self.calculator(nscfqe, stdin, incar=params)
            status = check.success(stdout,case)
            if not status['success']:
                check.write_status(status, stdout)
                return

            # step 2 : dos calculation %
            plt = {'prefix': case, 'ngauss': 1, 'deltae': 0.01, 'degauss': 0.02}
            if case == 'dos':
                plt = Incar(case, plt)
                plt['fildos'] = 'dos.plt.dat'
                self.plotter(nscfqe, incar=plt)
                if exists('dos.plt.dat'):
                    check.write_status(status, stdout)

            elif case == 'projwfc':
                plt = Incar(case, plt)
                plt['filpdos'] = 'p'
                plt['filproj'] = 'p'
                self.plotter(nscfqe, incar=plt)
                if exists('p.pdos_tot'):
                    check.write_status(status, stdout)
                    # move atom pdos 
                    if exists('pdos'):
                        shutil.rmtree('pdos')
                    os.makedirs('pdos')
                    for file in os.listdir(os.getcwd()):
                        if file.startswith('p.'):
                            shutil.move(file, join('pdos',file[2:]))

        else: # dos and so on
            params['calculation'] = 'nscf'
            params['prefix'] = case
            nscfqe = deepcopy(qe)
            stdout = self.calculator(nscfqe, stdin, incar=params)
            status = check.success(stdout,case)
            check.write_status(status, stdout)

        qe.tasks.nscf[case].finish = True
        # total status %
        if len(total) > 0 and np.array(total,dtype=bool).all():
            check.write_status(self.rootdir, status={'success':True}, task=stdout)
        return status 


    def _get_nband(self, qe, stdin=None):
	
        import numpy as np
        from os.path import join,exists
        from jamip.analysis.qe.qexml import GrepXml

        # get nbands from scf calculation %
        xmlfile = join(stdin+'.save','data-file-schema.xml') 
        if os.path.exists(xmlfile):
            nbands = GrepXml().nbnd(xmlfile)
        else:
            raise OSError('nbands grep failed.')
        # get nbands mutil %
        mutil = 1.2
        if hasattr(qe,'nbands'):
            mutil = qe.nbands
            
        if mutil < 3:
            nn = np.ceil(nbands*mutil/self.cluster.cores) * self.cluster.cores
        else:
            nn = mutil
        return int(nn)


    def get_band_kpath(self, structure, prec='suggest'):
        '''
        get hsym kpoints path base on structure.
        params:
            - prec: 
                  suggest: Continuous paths whose total length is greater than 5 segments.
                  all: All paths which time inversion are not considered
        '''
        from jamip.utils.brillouin_zone import HighSymmetryKpath
        from jamip.abtools.base.kpoints import __KPATH__, __KPT__
        import numpy as np

        bz = HighSymmetryKpath()
        kpoint = bz.get_HSKP(structure.bandStructure())

        kpaths = []
        for points in kpoint['Path']:
            # if add segments into suggest kpath % 
            if len(kpaths) and prec != 'all' and len(sum(kpaths,[]))-len(kpaths) > 5:
                num = 0
                for x,y in zip(kpath[-1].position, kpoint['Kpoints'][points[0]]):
                    num += min(abs(x-y), abs((x+y)-int(x+y)))
                if num > 0.001:
                    break
            kpath = []
            for p in points:
                kpath.append(__KPT__(p, kpoint['Kpoints'][p]))
            kpaths.append(kpath)

        return __KPATH__(kpaths)

    @property
    def realpath(self):
        from os.path import abspath,dirname,realpath
        return abspath(dirname(realpath(__file__)))

