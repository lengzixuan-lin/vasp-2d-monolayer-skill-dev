from .monitor import Monitor
from .check import CheckStatus
import os

class VaspFlow(object):

    def __init__(self, vasp=None, stdout=None, *args, **kwargs):

        from .tasks import TaskBuilder
        from .setvasp import SetVasp 
        from os.path import dirname,abspath,relpath
        from jamip.compute.cluster import Cluster

        # stdout directoty %
        if stdout:
            self.rootdir = abspath(stdout)
        else:
            self.rootdir = abspath(os.getcwd())
        submit_path = dirname(dirname(self.rootdir))
        path = relpath(self.rootdir,submit_path)
        # initialize cluster params %
        self.cluster = Cluster(submit_path)
        # classify the tasks % 	
        if isinstance(vasp, SetVasp):
            vasp._tasks_ = TaskBuilder.create(vasp.tasks,submit_path,path)
            vasp.tasks.set_energy(vasp.energy)
            vasp.tasks.set_force(vasp.force)
        else:
            raise TypeError('Invalid func. Make sure you input a SetVasp class!')
        
        self.vasp_calculator(vasp, stdout)

    def exit(self,vasp):
        for key in vasp.tasks:
            if vasp.tasks[key] != None:
                vasp.tasks[key].finish = True
	
    def vasp_calculator(self, vasp, stdout, stdin=None, **kwargs):
        
        from copy import deepcopy
        from os.path import exists, join, abspath 
        from .tasks import TaskBuilder
        from .monitor import CPUcheck 
        from ..diyflow import import_diy_module
	
        CPUcheck.write_cluster_status(self.cluster.cores)

        if exists(stdout) and exists(join(stdout,'.status')):
            stdin = CheckStatus._continue(vasp.tasks, self.rootdir, overwrite=vasp.overwrite)

        print('Job start from :', stdin)

        # converge-test %
        if vasp.tasks.converge is not None:
            diy_class = import_diy_module('converge')
            diyflow = diy_class(func=deepcopy(vasp),stdin=stdin,rootdir=self.rootdir)
            return

        # optimization % 
        if vasp.tasks.relax is not None and vasp.tasks.relax.finish is False:
            output = join(stdout, 'relax')
            stdin = self.relax_cell_ions(vasp, output, stdin)

            # exit calculation-flow if task error % 
            if vasp.tasks.relax.finish == False:
                print("Stop calculation because optimize calculation is not converged.")
                self.exit(vasp)

        # md calculation %
        if vasp.tasks.md is not None and vasp.tasks.md.finish is False:
            output = join(stdout, 'md')
            self.molecular_dynamics(vasp, output, stdin)

        # single point calculation %
        if vasp.tasks.scf is not None and vasp.tasks.scf.finish is False:
            output = join(stdout, 'scf')
            stdin = self.single_point(vasp, output, stdin)

            # exit calculation-flow if task error % 
            if vasp.tasks.scf.finish == False:
                print("Stop calculation because scf calculation is not converged.")
                self.exit(vasp)

        if vasp.tasks.scf is None and stdin is None:
            print("Stop calculation because no scf calculation.")
            self.exit(vasp)

        # properties calculation %
        for key in TaskBuilder().property: 
            if key in vasp.tasks and vasp.tasks[key].finish is False:
                for prop in vasp.tasks[key]:
                    if vasp.tasks[key][prop].finish is False:
                        self.calc_property(key, vasp, prop, stdin, stdout) 
		
        # diy calculation %
        if vasp.tasks.diy is not None and vasp.tasks.diy.finish is False:
            for key in vasp.tasks.diy:
                if vasp.tasks.diy[key].finish is False:
                    diy_class = import_diy_module(key)
                    diyflow = diy_class(func=deepcopy(vasp),stdin=stdin,rootdir=self.rootdir)

        print('Calculation finished')

    def calc_property(self,case,vasp,prop,stdin,stdout):
        output = os.path.join(stdout, case, prop) 
        try:
            if case == 'electric':
                self.electric_property(vasp, prop, stdin, output) 
            elif case == 'magnetic':
                self.magnetic_property(vasp, prop, stdin, output) 
            elif case == 'optic':
                self.optic_property(vasp, prop, stdin, output) 
            elif case == 'phonon':
                self.phonon_property(vasp, prop, stdin, output) 
            elif case == 'mechanic':
                self.mechanic_property(vasp, prop, stdin, output) 
        except BaseException as e:          
            print('%s calculation failed!')         
            print('Error :', e)
  
    @Monitor
    def calculator(self, vasp, stdout=None, stdin=None, incar={}, overwrite=True, **kwargs):

        from os.path import join, exists, getsize 
        import shutil
        import os  

        # restart from previous calculation % 
        if stdin is not None:

            # udpate the structure % 
            self.load_structure(vasp,stdin)

            if stdin != stdout:
                if not exists(stdout): os.makedirs(stdout)
                overwrite = True 

                # copy chgcar %
                chgin = join(stdin,'CHGCAR')
                chgout = join(stdout,'CHGCAR')
                if exists(chgin) and getsize(chgin):
                    if 'icharg' not in incar:
                        incar['icharg'] = 1
                elif 'icharg' not in incar:
                    incar['icharg'] = 2
                elif incar['icharg'] == 11:
                    raise IOError('CHGCAR not exists!')

                if incar['icharg'] == 1 or incar['icharg'] == 11:
                    if 'lcharg' in incar and incar['lcharg'] == False:
                        if exists(chgout): os.remove(chgout)
                        os.symlink(chgin,chgout)
                    else:
                        shutil.copyfile(chgin,chgout)

                # copy wavecar %
                wavein = join(stdin,'WAVECAR')
                waveout = join(stdout,'WAVECAR')
                if exists(wavein) and getsize(wavein):
                    if 'istart' not in incar:
                        incar['istart'] = 1
                else:
                    incar['istart'] = 0

                if incar['istart'] == 1:
                    if 'lwave' in incar and incar['lwave'] == False:
                        if exists(waveout): os.remove(waveout)
                        os.symlink(wavein,waveout)
                    else:
                        shutil.copyfile(wavein,waveout)

        incar = vasp.set_input(vasp.structure, stdout, overwrite, incar)

        # run vasp progam % 
        self.run(stdout, program=self.get_program(vasp,incar)) 
        return stdout 

    # run % 
    def run(self, stdout=None, program=None):

        import os 
        from os.path import join
        os.chdir(join(self.rootdir,stdout))
	
        try:
            cmd = "{mpi} {program} > pbs.log".format(mpi=self.cluster.run, program=program)
        except:   
            raise AttributeError("VaspFlow.cluster object has no attribute 'mpi' or 'cores'")

        os.popen(cmd).readline()
        os.chdir(self.rootdir)

    def molecular_dynamics(self, vasp, stdout, stdin=None, **kwargs):

        from os.path import join, exists
        import numpy as np
        import re

        steps = []
        if exists(stdout):
            for dir in os.listdir(stdout):
                steps.extend(re.findall('^S(\d+)$',dir))

        if len(steps) == 0:
            stdout = join(stdout,'S1')
        else:
            num = np.array(steps, dtype=int).max()
            stdin = join(stdout,'S{}'.format(num))
            stdout = join(stdout,'S{}'.format(num+1))

        # task start %
        self.calculator(vasp, stdout, stdin, incar=vasp.tasks.md)

        # check force convergence or not, default is force% 
        check = CheckStatus(self.rootdir) 

        # check status % 	
        status = check.success(join(stdout,'OUTCAR'), task='md')
        check.write_status(status, stdout)
        if status['success']:
            vasp.tasks.scf.finish = True

        return stdout
 
    def single_point(self, vasp, stdout, stdin=None, **kwargs):
	
        from os.path import join

        # task start %
        self.calculator(vasp, stdout, stdin, incar=vasp.tasks.scf)

        # check force convergence or not, default is force% 
        check = CheckStatus(self.rootdir) 

        # check status % 	
        status = check.success(join(stdout,'OUTCAR'), task='scf')
        check.write_status(status, stdout)
        if status['success']:
            vasp.tasks.scf.finish = True

        return stdout
	
    def relax_cell_ions(self, vasp, stdout, stdin=None, steps=3, **kwargs):
        """
        function to relax the cell shape, internal inons and volume.
        """
        from os.path import join  
        from .tasks import VaspIncar
        import shutil
        import re

        # check force convergence or not, default is force% 
        check = CheckStatus(self.rootdir) 

        # get accelerate parameter % 
        if getattr(vasp,'accelerate',True):
            if isinstance(vasp.accelerate,list):
                accelerate = vasp.accelerate
            elif isinstance(vasp.accelerate,bool):
                step1 = {'kspacing':0.5, 'ediff':1E-3, 'nsw':20, 'istart': 0, 'icharg': 2}
                step2 = {'kspacing':0.4, 'ediff':1E-4, 'ediffg':-0.05, 'nsw':20, 'istart': 0, 'icharg': 2}
                vasp.accelerate = [step1,step2]
                accelerate = vasp.accelerate

            # run vasp object % 
            for acc in accelerate:
                acc.downdate(vasp.tasks.relax) 
                if 'isif' in acc and acc['isif']== -1:
                    acc['isif'] = 7
                    stdin = self.calculator(vasp, stdout+'/S0', stdin, overwrite=True, incar=acc)
                    acc['isif'] = 2  
                    stdin = self.calculator(vasp, stdout+'/S0', stdin, overwrite=True, incar=acc)
                else:	
                    stdin = self.calculator(vasp, stdout+'/S0', stdin, overwrite=True, incar=acc)
       
            # check accelerate status % 	
            status = check.success(join(stdin,'OUTCAR'))
            check.write_status(status, stdin)

        n = 1
        success = False
        last_status = None
        params = vasp.tasks.relax 
        # run vasp object % 
        while (n <= steps) and (not success):
            subout = join(stdout,'S'+str(n))
            if 'isif' in params and params['isif']== -1: # (iv) 
                params['isif'] = 7 
                stdin = self.calculator(vasp, subout, stdin, incar=params)
                params['isif'] = 2 
                stdin = self.calculator(vasp, subout, stdin, incar=params)
            else:
                stdin = self.calculator(vasp, subout, stdin, incar=params)

            status = check.success(join(stdin,'OUTCAR'))
            check.write_status(status, stdin)
            success = status['success']
            n += 1
            if status['finish']:
                status['task'] = 'relax'
                last_status = status,stdin

        for dir in os.listdir(stdout):
            if re.match('^S\d+$',dir) and int(dir[1:]) >= n:
                shutil.rmtree(join(stdout,dir)) 

        if success:
            vasp.tasks.relax.finish = True
            status['task'] = 'relax'
            check.write_status(status, stdin)
        elif last_status != None:
            check.write_status(*last_status)
            # converge finish %
            if vasp.converge and check.is_converge(stdin):
                print("Warning! relax calculation is unfinished but converged. Calculation will continue")
                vasp.tasks.relax.finish = True
        
        return stdin
  
    def electric_property(self, vasp, case, stdin, stdout, **kwargs):

        """
        select the case of tasks
        """
        from jamip.analysis.vasp import BandFinder
        from os.path import join, exists, dirname
        from copy import deepcopy
        import numpy as np

        # get incar params %
        params = vasp.tasks.electric[case]
        check = CheckStatus(self.rootdir) 
        total = []

        if case == 'band':
            # copy vasp and change vasp.kpoints %
            bandvasp = deepcopy(vasp)
            # get kpath - input.py or automatic generation % 
            band = self.get_band_kpath(vasp, stdin, task='band')

            # get nbands %
            if 'nbands' not in params:
                params['nbands'] = self.get_nband(vasp,stdin)

            # loop the kpoints % 
            if getattr(vasp,'band_split',False):
                for k, kpath in band.split(): 
                    bandvasp.kpoints = kpath
                    subout = self.calculator(bandvasp, join(stdout,k), stdin, incar=params)
                    status = check.success(join(subout,'OUTCAR'))
                    check.write_status(status, subout)
                    total.append(status['success'])
 
            else:
                bandvasp.kpoints = band
                self.calculator(bandvasp, stdout, stdin, incar=params)
                status = check.success(join(stdout,'OUTCAR'),case)
                check.write_status(status, stdout)

        elif case == 'partchg':
            # step 1 : get band edge
            edge = self.get_band_edge(vasp, stdin)
            # check whether a nogap bandstructure %
            if edge['gap'] < 0: 
                check.error_status(error='no-gap', path=stdout)
                return False

            # get kpoints with weight %
            bf = BandFinder(stdin)
            kpt = bf._get_kpoint(stdin,weight=True)
            for i in ['cbm','vbm']:
                k = np.append(edge[i]['kpoint'],0.01)
                kpt=np.vstack((kpt,k))

            # step 2 : calculation again, add cbmvbm into kpoints %
            if not exists(stdout): os.makedirs(stdout)
            # scf with bandedge kpoints %
            partchgvasp = deepcopy(vasp)
            partchgvasp.kpoints = ("Reciprocal",kpt)
            stdin = self.calculator(partchgvasp, join(stdout,'scf'), stdin, incar=vasp.tasks.scf)
            status = check.success(join(stdin,'OUTCAR'))
            check.write_status(status, stdin)
            if not status['success']: return False

            # get iband %
            bf.stdin = stdin
            cb,vb = bf.get_cbvb()[0]

            # cbm partchg %
            params['kpuse'] = len(kpt)-1
            params['iband'] = cb+1
            subout = self.calculator(partchgvasp, join(stdout,'cbm'), stdin, incar=params)
            status = check.success(join(stdout,'cbm','OUTCAR'))
            check.write_status(status, subout)
            total.append(status['success'])

            # vbm partchg %
            params['kpuse'] = len(kpt)
            params['iband'] = vb+1
            subout = self.calculator(partchgvasp, join(stdout,'vbm'), stdin, incar=params)
            status = check.success(join(stdout,'vbm','OUTCAR'))
            check.write_status(status, subout)
            total.append(status['success'])


        elif case == 'emass':
            # step 1 : get band edge and set emass path %
            edge = self.get_band_edge(vasp, stdin)
            # check whether a nogap bandstructure %
            if edge['gap'] < 0: 
                check.error_status(error='no-gap', path=stdout)
                return False

            # get nbands %
            params.downdate(vasp.tasks.electric['band'])
            if 'nbands' not in params:
                params['nbands'] = self.get_nband(vasp, stdin)
	
            bandvasp = deepcopy(vasp)
            band = self.set_emass_band(edge)
            # loop the kpoints % 
            for dir,kpath in band.items(): 
                bandvasp.kpoints = kpath
                subout = self.calculator(bandvasp, join(stdout,dir), stdin, incar=params)
                status = check.success(join(stdout,dir,'OUTCAR'))
                check.write_status(status, subout)
                total.append(status['success'])

        elif case == 'hse_gap':
                
            # step 1: get band edge % 
            edge = self.get_band_edge(vasp, stdin)
            if edge['gap'] < 0: 
                check.error_status(error='no-gap', path=stdout)
                return False

            # get kpoints with weight %
            bf = BandFinder(stdin)
            kpt = bf._get_kpoint(stdin,weight=True)
            for i in ['cbm','vbm']:
                k = np.append(edge[i]['kpoint'],0.0)
                kpt=np.vstack((kpt,k))

       	    # step 2: calculate HSE gap %    	
            hsevasp = deepcopy(vasp)
            hsevasp.kpoints = ("Reciprocal",kpt)
            hsevasp._xc_.add('hse')
            self.calculator(hsevasp, stdout, stdin, incar=params)
            status = check.success(join(stdout,'OUTCAR'),case)
            check.write_status(status, stdout)

        else: # dos and others %
            self.calculator(vasp, stdout, stdin, incar=params)
            # check_stutus % 
            status = check.success(join(stdout,'OUTCAR'),case)
            check.write_status(status, stdout)

        # finished %
        vasp.tasks.electric[case].finish = True
        # total status %
        if len(total) > 0 and np.array(total,dtype=bool).all():
            status={'task':case,'finish':True,'success':True}
            check.write_status(status, stdout)
        return status 
	 
    def phonon_property(self, vasp, case, stdin, stdout, **kwargs):

        """
        select the case of phonon tasks
        """
        from os.path import join, exists,relpath
        from phonopy.structure.atoms import PhonopyAtoms
        from jamip.structure.convert import phonopy2jamip
        from phonopy import Phonopy
        from copy import deepcopy
        import numpy as np


        # initialize structure %
        structure = self.load_structure(vasp,stdin)
        unitcell = PhonopyAtoms(cell = structure.lattice,
                       scaled_positions = structure.get_positions(),
                       symbols = structure.get_elements('symbol')
                       )

        # get incar params %
        params = vasp.tasks.phonon[case]
        symprec = vasp.tasks.phonon.force.symprec
        dim = vasp.tasks.phonon.force.dim

        # inistalize class %
        phonon = Phonopy(unitcell,dim,symprec=symprec)
        phonon.generate_displacements()
        phononvasp = deepcopy(vasp)
        check = CheckStatus(self.rootdir) 
        subtasks = []

        if case == 'force':

            for i,supercell in enumerate(phonon.supercells_with_displacements):
                subout = join(stdout,'mode'+str(i))
                incar = vasp.set_input(phonopy2jamip(supercell), subout, True, params)
                subtasks.append(subout)


        elif case == 'softmode':
            # update phonon force %
            phonon = self.get_force_set(vasp, phonon)
            parallel = params.parallel
            amplitude = params.amplitude
            # softmode set %
            softmode = []
            if len(amplitude) == 1:
                x = params.amplitude[0]
                softmode.append([q,params.band_index,x,params.argument])
            elif len(amplitude) == 3:
                for x in np.arange(amplitude[0],amplitude[1],amplitude[2]):
                    softmode.append([params.q,params.band_index,x,params.argument])
            phonon.set_modulations(params.dim,softmode)

            for i,supercell in enumerate(phonon.get_modulated_supercells()):
                subout = join(stdout,'mode'+str(i))
                incar = vasp.set_input(phonopy2jamip(supercell), subout, True, params)
                subtasks.append(subout)

        elif case == 'gruneisen':
            from jamip.analysis.vasp import PhononFinder
            scale_factor = {"minus": 1-params.scale,
                            "plus" : 1+params.scale,}
            phonon = self.get_force_set(vasp, phonon)
            parallel = params.parallel
            if vasp.tasks.scf != None:
                params.downdate(vasp.tasks.scf)

            for key, scale in scale_factor.items():
                # relax %
                phononvasp.structure = deepcopy(structure)
                phononvasp.structure.scale_factor = scale
                stdin = self.calculator(phononvasp, join(stdout,key,'relax'), stdin=None, incar=params)
                status = check.success(join(stdin,'OUTCAR'))
                check.write_status(status, stdin)

                # inistalize class %
                structure = self.load_structure(phononvasp,stdin)
                unitcell = PhonopyAtoms(cell = structure.lattice,
                       scaled_positions = structure.get_positions(),
                       symbols = structure.get_elements('symbol')
                       )
                phonon = Phonopy(unitcell,dim,symprec=symprec)
                phonon.generate_displacements()

                # force %
                for i,supercell in enumerate(phonon.supercells_with_displacements):
                    subout = join(stdout,key,'force','mode'+str(i))
                    incar = vasp.set_input(phonopy2jamip(supercell), subout, True, incar=vasp.tasks.phonon.force)
                    subtasks.append(subout)

        program = self.get_program(vasp, incar)
        parallel = min(len(subtasks),params.parallel)
        self.subtask_calculation(vasp, subtasks, case, program, parallel)

        return True


    def subtask_calculation(self, vasp, subtasks:list, case:str, program:str, parallel:int):

        from collections import OrderedDict
        from os.path import join, relpath, dirname
        from ruamel import yaml
        import numpy as np
        import re

        if parallel == 1:
            check = CheckStatus(self.rootdir) 
            total = []

            for stdout in subtasks:
                self.run(stdout, program)
                status = check.success(join(stdout,'OUTCAR')) 
                # check.write_status(status, stdout)
                total.append(status['success'])

            if len(total) > 0 and np.array(total,dtype=bool).all():
                status={'task':case,'finish':True,'success':True}
                vasp.tasks.phonon[case].finish = True
                key = re.findall('[A-Za-z]*/%s/'%case, relpath(stdout,self.rootdir))
                path = key[0] if len(key) else dirname(path)
                check.write_status(status, path)


        elif parallel > 1:

            # continue %
            with open('pbsscript','r') as f:
                cmd = f.readlines()[-1].split()
                poolfile = cmd[2]
         
            # base running params %
            pool = OrderedDict()
            pool['configuration'] = {
                'soft': 'vasp',
                'task': case, 
                'manager': self.cluster['manager'],
                'pool': poolfile,
                'program': program,
                'rootdir': self.rootdir,
                'parallel': parallel, }

            for subout in subtasks:
                key = relpath(subout,self.rootdir)
                pool[key] = {
                    'priority': 0,
                    'status': 'wait',
                    'success': None,
                    'host': None}
            with open('subtask.yaml','w') as f:
                yaml.dump(pool, f, Dumper=yaml.RoundTripDumper)
         
            self.cluster.script = 'subscript'
            self.cluster.write_script('subtask.yaml',self.rootdir,'compute/queues.py')
            print('Mainjob finish. subtask start.')
            self.exit(vasp)
         
            # submit jobs %
            for i in range(parallel):
                os.popen('%s subscript' %self.cluster.cmd).readline()


    def get_force_set(self, vasp, phonon, property=True):
        from os.path import join,exists
        from jamip.analysis.vasp import PhononFinder
        from phonopy.file_IO import parse_FORCE_SETS

        filename = join(self.rootdir,'FORCE_SETS')
        if exists(filename):
            print('phonon_force_set existed.')
        else:
            if property and not vasp.tasks.phonon.force.finish:
                output = join(self.rootdir,'phonon','force')
                self.phonon_property(vasp, 'force', None, output)

            pf = PhononFinder(self.rootdir)
            forces = pf.get_forces()
            pf.write_forces(phonon,forces,filename)
            print('phonon_force calculation finished.')

        if not exists(filename): 
            raise RuntimeError("Failed in read FORCE_SETS.")

        force_sets=parse_FORCE_SETS(filename=filename)
        phonon.set_displacement_dataset(force_sets)
        phonon.produce_force_constants(calculate_full_force_constants=False)
        return phonon

    def mechanic_property(self, vasp, case, stdin, stdout, **kwargs):
        """
        select the case of optic tasks
        """
        from os.path import join, exists
        params = vasp.tasks.mechanic[case]
        check = CheckStatus(self.rootdir) 
        
        if case == 'elastic':
            params['npar'] = 1
            self.calculator(vasp, stdout, stdin, incar=params)
            # check_stutus % 
            status = check.success(join(stdout,'OUTCAR'),case)
            check.write_status(status, stdout)

        # finished %
        vasp.tasks.mechanic[case].finish = True
        return True

 

    def optic_property(self, vasp, case, stdin, stdout, **kwargs):

        """
        select the case of optic tasks
        """
        from os.path import join, exists
        from copy import deepcopy
        import numpy as np

        # get incar params %
        params = vasp.tasks.optic[case]
        check = CheckStatus(self.rootdir) 


        if case == 'optics':
            # get nbands %
            if 'nbands' not in params:
                params['nbands'] = self.get_nband(vasp,stdin)
            params.update(kwargs)

            self.calculator(vasp, stdout, stdin, incar=params)
            # check_stutus % 
            status = check.success(join(stdout,'OUTCAR'),case)
            check.write_status(status, stdout)

        elif case == 'gw':

            # step 0: calculate optics %
            if vasp.tasks.optic['optics'].finish == False:
                output = os.path.join(self.rootdir,'optic','optics')
                optics_params = {'isym':0, 'lwave':True}
                self.optic_property(vasp, case, stdin, output, **optics_params)
            if vasp.tasks.optic['optics'].finish == False:
                check.error_status(error='no-optics', path=stdout)
                return False

       	    # step 1: calculate GW gap %    	
            stdin = os.path.join(self.rootdir,'optic','optics')
            if not exists(stdout): os.makedirs(stdout)
            os.system('cp {0}/WAVECAR {1}/WAVECAR.DIAG'.format(stdin,stdout))
            os.system('cp {0}/WAVEDER {1}/WAVEDER.DIAG'.format(stdin,stdout))

            gwvasp = deepcopy(vasp)
            gwvasp._xc_.add('gw')
            self.calculator(gwvasp, stdout, stdin, params)
            status = check.success(join(stdout,'OUTCAR'),case)
            check.write_status(status, stdout)

        elif case == 'born' or case == 'dielectric':
            if 'lepsilon' in params and params['lepsilon'] == True:
                params['npar'] = self.cluster.cores 
            self.calculator(vasp, stdout, stdin, incar=params)
            # check_stutus % 
            status = check.success(join(stdout,'OUTCAR'),case)
            check.write_status(status,stdout)
	 
        vasp.tasks.optic[case].finish = True
        return status 


    def get_nband(self, vasp, stdin=None):
	
        import numpy as np
        from jamip.analysis.vasp.outcar import GrepOutcar

        # get nbands from scf calculation %
        if stdin != None and os.path.exists(stdin):
            nbands = GrepOutcar().nbands(stdin) 
        else:
            raise IOError('nbands grep failed.')
        # get nbands mutil %
        mutil = 1.2
        if hasattr(vasp,'nbands'):
            mutil = vasp.nbands
            
        if mutil < 3:
            nn = np.ceil(nbands*mutil/self.cluster.cores) * self.cluster.cores
        else:
            nn = mutil
        return int(nn)

    def set_emass_band(self, edge):
        ''' set emass kpath  '''
        from jamip.abtools.base.kpoints import __KPATH__
        import numpy as np

        _axis = {0:'x',1:'y',2:'z'}
        cbm = edge['cbm']['kpoint']
        vbm = edge['vbm']['kpoint']
        minus = np.abs(cbm - vbm)
        index = np.arange(3)
        bands = {}

        for i in range(3):
            if np.sum(minus[np.where(index != i)]) < 0.001:


                kpath = np.array([vbm,vbm])
                kpath[:,i] = [0,0.5] 
                bands[_axis[i]+'-cbm-vbm'] = kpath

            else:
                # cbm %
                kpath = np.array([cbm,cbm])
                kpath[:,i] = [0,0.5]
                bands[_axis[i]+'-cbm'] = kpath
                # vbm %
                kpath = np.array([vbm,vbm])
                kpath[:,i] = [0,0.5]
                bands[_axis[i]+'-vbm'] = kpath

        for key in bands:
            bands[key] = __KPATH__._from_array(bands[key])

        return bands

    def get_band_edge(self, vasp, stdin=None, banddir=None):
        from os.path import join,isdir,isfile
        from jamip.analysis.vasp import BandFinder
        from ..vasp.check import CheckStatus

        status = CheckStatus.load_status(self.rootdir)

        # check if bandstructure is finished %
        finish = False
        if 'band' in status and status['band'].finish is True:
            finish = True
        else:
            status = self.electric_property(vasp, 'band', stdin,
                              join(self.rootdir, 'electric', 'band'))
            finish = status['success']

        if not finish:
            raise IOError ('Failed in calculation band structure!')

        try:
            bd = BandFinder(self.rootdir)
            edge = bd.get_cbmvbm()
        except:
            raise IOError ('Error! cannot find cbmvbm')
        #if edge['gap'] < 0:
        #    raise IOError ('Error! The band gap is less than 0!')

        return edge

    def get_band_kpath(self, vasp, stdin, task=None, insert=30, prec='suggest'):
        '''
        get hsym kpoints path base on structure.
        params:
            - prec: 
                  suggest: Continuous paths whose total length is greater than 5 segments.
                  all: All paths which time inversion are not considered
        '''	
        from jamip.utils.brillouin_zone import HighSymmetryKpath
        from jamip.abtools.base.kpoints import __KPATH__, __KPT__, Kpoints
        import numpy as np

        if task != None and task in vasp.kpath:
            if isinstance(vasp.kpath[task], Kpoints):
                return vasp.kpath[task].kpoints
            elif isinstance(vasp.kpath[task], int):
                insert = vasp.kpath[task]

        bz = HighSymmetryKpath()
        structure = self.load_structure(vasp,stdin)
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
 
        return __KPATH__(kpaths, insert)

    @property
    def realpath(self):
        from os.path import abspath,dirname,realpath
        return abspath(dirname(realpath(__file__)))

    def load_structure(self,vasp,stdin=None):
        from jamip.structure import read
        from os.path import exists,join

        # read structure %
        if stdin != None and exists(stdin):
            try:
               vasp.structure = read(join(stdin,'CONTCAR'))
            except:
                try:
                   vasp.structure = read(join(stdin,'POSCAR'))
                except:
                   pass

        return vasp.structure

    def get_program(self, vasp, incar):

        if isinstance(vasp.program, dict):
            if 'lsorbit' in incar or'LSORBIT' in incar:
                if 'ncl' not in vasp.program:
                    raise KeyError('Non-collinear version of the VASP is required for SOC calculations')
                program = vasp.program['ncl'] 
            else:
                program = vasp.program['std']
        else:
            program = vasp.program

        return program
