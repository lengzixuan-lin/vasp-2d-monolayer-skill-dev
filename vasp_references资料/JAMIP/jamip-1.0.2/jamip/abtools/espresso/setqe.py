# 1. write structure % 
# 2. write potentials % 
# 3. write kpoints % 
# 4. write incar % 

import os 
from ..base.kpoints import Kpoints 
from .tasks import Tasks
from .qeio import QEIO

class SetQE(Tasks,Kpoints,QEIO):

    def __init__(self):
        Kpoints.__init__(self)
        super().__init__()
        self.__program = None 
        self.__tasks_ = None 
        self.__xc_ = None
        self._accelerate_ = True
        self.__files = set()
        self.overwrite = False
        self.converge = False
   	
    def set_input(self, structure, incar, **kwargs):
    
        """
        set INCAR/POSCAR/POTCAR/KPOINTS/additional_files 
        """
        from os.path import exists, join 
        #from .tasks import VaspIncar

        qeinput = incar['prefix']+'.in'
        with open(qeinput,'w+') as self.fopen:

            # &ATOMIC_SPECIES % 
            incar.update(self.set_potential(structure))

            # CELL_PARAMSTERS - ATOMIC_POSITIONS % 
            incar.update(self.set_structure(structure))
            
            # &K_POINTS: set kmesh % 
            if 'kspacing' in incar:
                self.kpoints = incar.pop('kspacing')
            self.set_kpoints(structure)
         
            # VDW % 
            # Magnetic moment % 
            # incar.update(self.set_magmom(structure,**incar))	
            # LDA+U % 
            # incar.update(self.set_ldau(structure))	
         
            # INPUT: write input %
            incar = self.write_input(incar)
     	   
            # external file %
            #self.set_externalfile(stdout)
        del self.fopen

        return incar

    # is ispin=2 or lsorbit=True % 
    def get_spin(self,incar):

       	spin = False 
        # magnetic property % 
        if 'lsorbit' in incar and 't' in str(incar['lsorbit']).lower():
            spin = True
        elif 'ispin' in incar: 
            if incar['ispin'] == 2:
                spin = True
        elif 'ispin' in self.tasks.default and self.tasks.default['ispin'] == 2: 
            spin = True

        return spin

    # set_external file % 
    def set_externalfile(self, stdout=None):
        
        from os.path import join, exists, abspath 
        
        if not exists(abspath(stdout)): os.makedirs(stdout)

        # OPTCELL %
        if hasattr(self, 'optcell'):
            with open(join(stdout,'OPTCELL'),'w') as f:
                f.write(self.__optcell)

        # external-file %
        if hasattr(self,'external_files'):
            for path in self.external_files:
                if "vdw_kernel" in path: continue
                os.system('cp -r {0}  {1}'.format(path, stdout))	

    # set potential %
    def set_potential(self,structure):
        """
        Set the POTCAR according to the species of elements in structure.
        
        return dict{'ecutwfc':wfc, 'ecutrho':rho}
        """	
         
        import re 
        import numpy as np
        from os.path import join, exists, abspath 
        from .utils import EspressoPotentials,EspressoElements

        elements = list(structure.species_of_elements)
        description = '(rel)?-?(starNl|starhNl)?-?(pz|vwn|pbe|blyp|pw91|tpss|column)-?([spdfnl]*)-(ae|mt|bhs|vbc|van|rrkj|rrkjus|kjpaw|bpaw)[^a-zA-Z0-9]'

        pseudo_dir = None
        pseudo_user = None
        if isinstance(self.potential,tuple):
            assert len(self.potential) == 2
            pseudo_dir, pseudo_user = self.potential
        elif isinstance(self.potential,str):
            pseudo_dir = self.potential

        pseudo_lib = EspressoPotentials(pseudo_dir)
        pots = [None]*len(elements)

        # set potential by custom %
        if pseudo_user != None: 
            for i,elm in enumerate(elements):
                if elm in pseudo_user and pseudo_user[elm] in pseudo_lib[elm]: 
                    pots[i] = pseudo_user[elm]

        # set potential by auto %
        qe_pseudo = 'rrkjus'
        if hasattr(self,'pseudo'):
            qe_pseudo = self.pseudo

        qe_xc = 'pbe'
        if hasattr(self,'potxc'):
            qe_pseudo = self.potxc

        for i,elm in enumerate(elements):
            if pots[i] != None: continue
            options = []
            if elm not in pseudo_lib:
                raise KeyError("No useable potential for %s in the pseudopotential library !" %symbol)
            for pot in pseudo_lib[elm]:
                _,_,xc,state,pseudo = re.findall(description,pot)[0]
                if xc == qe_xc and pseudo == qe_pseudo:
                    options.append((state,pot))
           
            # select potential %
            if len(options) == 0:
                raise KeyError("No useable pseudopotential for %s in the pseudopotential library ." %e)
            elif len(options) == 1:
                pots[i] = options[0][1] 
            elif len(options) > 1:
                n = np.argmin([len(i[0]) for i in options])
                pots[i] = options[n][1] 

        # read potentials %
        options = []
        wfcs = []
        rhos = []
        for elm,pot in zip(elements,pots):

            # set mass %
            if elm in EspressoElements:
                mass = EspressoElements[elm][1]
            else:
                raise Keyerror('Element %s not in mass dict')

            options.append([elm,mass,pot])

            # search wfc&rho
            wfc = rho = None
            with open(join(pseudo_dir, pot),'r') as f:
                for line in f:
                    if 'wavefunctions' in line:
                        wfc = re.findall(r':\s*(\d+\.?\d*)\s+Ry',line)[0]
                    elif 'charge density' in line:
                        rho = re.findall(r':\s+(\d+\.?\d*)\s+Ry',line)[0]
                    if wfc and rho:
                        break    
            wfcs.append(wfc)
            rhos.append(rho)
                    
        # update cutoff params %
        maxwfc = np.max(np.array(wfc,dtype=float))
        maxrho = np.max(np.array(rho,dtype=float))
        if hasattr(self,'ecutwfc'):
            if self.ecutwfc > 30:
                maxwfc = min(self.ecutwfc,150)
            else:
                maxwfc = min(self.ecutwfc*maxwfc,150)
        if hasattr(self,'ecutrho'):
            if self.ecutrho > 100:
                maxrho = min(self.ecutrho,1200)
            elif self.ecutrho >= 6:
                maxrho = min(self.ecutrho*maxwfc,1200)
            else:
                maxrho = min(self.ecutrho*maxrho,1200)

        params = {'ecutwfc': maxwfc,
                  'ecutrho': maxrho,
                  'pseudo_dir': pseudo_dir}
        # &POTENTIAL % 
        self.fopen = self.write_potential(options,self.fopen)

        return params

    # set structure %
    def set_structure(self, structure):


        elements = structure.species_of_elements
        params = {'ntyp': len(elements),
                  'nat': sum(structure.number_of_atoms)}

        # &POSITIONS %  		
        self.fopen = self.write_structure(structure, self.fopen)

        return params

    def set_kpoints(self, structure, **kwargs):
        """
        """
        import numpy as np
        if self.model == 'kspacing':
            rec_lattice = np.linalg.inv(structure.lattice)*2*np.pi
            kmesh = []
            for v in rec_lattice:
                kmesh.append(np.ceil(np.linalg.norm(v)/self.kpoints))
            self.kpoints = ('Gamma',kmesh)

        self.fopen = self.write_kpoints(self.fopen)

        return {}


    def set_vdw(self, elements=None, stdout=None):
        """
        """
        pass

    def write_input(self, incar):

        incar.downdate(self.tasks.base) 
        self.write_pwscf(incar,self.fopen)

        return incar
           
    @property 
    def program(self):
        return self.__program 

    @program.setter
    def program(self, value=None):
        if isinstance(value,str) and os.path.isdir(value):
            self.__program = value 
        else:
            raise IOError ('invalid input VASP program')
