# 1. write poscar % 
# 2. write potcar % 
# 3. write kpoints % 
# 4. write incar % 
# 5. write vdwkernel % 

from .tasks import Tasks,Incar
from ..base.kpoints import Kpoints 
from .vaspio import VaspIO
from .vdw import VDW
from typing import Union
import os 
class SetVasp(Tasks,Kpoints,VDW,VaspIO):

    def __init__(self):
        super().__init__()
        Kpoints.__init__(self)
        self._kpoints_ = None
        self.__program = None
        self.__files = set()
        self.__pot = None
        self.overwrite = False
        self.converge = False
   	
    def set_input(self, structure, stdout, overwrite=True, incar=None, **kwargs):
    
        """
        set INCAR/POSCAR/POTCAR/KPOINTS/additional_files 
        """
        from os.path import exists, join 

        if not exists(stdout): 
            overwrite = True 

        if not isinstance(incar,Incar):
            incar = Incar('input',incar)

        incar.update(kwargs)

        if overwrite is True:
            
            # POTCAR: set pseudopotential % 
            incar.encut = self.set_potcar(structure, stdout)
            
            # KPOINTS: set kmesh % 
            incar.update(self.set_kpoints(stdout, incar))

            # xc_func %
            for xc_func in self.xc_func:
                 if xc_func.lower() in ['soc','gw','hse']:
                     incar.update_params(self.tasks.xc[xc_func])
                 else:
                     incar['gga'] = xc_func

            # VDW % 
            if incar.name in self.vdw_tasks:
                incar.update_params(self.set_vdw(structure, stdout))
                

            # Magnetic moment % 
            # incar.update(self.set_magmom(structure,**incar))	

            # LDA+U % 
            # incar.update(self.set_ldau(structure))	

            # POSCAR: set poscar %  		
            self.write_poscar(structure, stdout, name='POSCAR')
    	
            # external file %
            self.set_externalfile(stdout)

            # INCAR: write incar %
            incar = self.set_incar(incar, stdout)    

        return incar

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
        
    # set POTCAR % 
    def set_potcar(self, structure, stdout, name='POTCAR'):

        """
        Set the POTCAR according to the species of elements in structure.
        
        return dict{'ENMAX':enmax}
        """	
         
        import re
        import numpy as np
        from .utils import VaspPotentials

        elements = list(structure.species_of_elements)
        pseudo_dir = None
        pseudo_user = None
        if isinstance(self.potential,tuple):
            assert len(self.potential) == 2
            pseudo_dir, pseudo_user = self.potential
        elif isinstance(self.potential,str):
            pseudo_dir = self.potential

        potlib = VaspPotentials(pseudo_dir)
        pots = [None]*len(elements)

        # set potential by custom %
        if pseudo_user != None: 
            for i,elm in enumerate(elements):
                if elm in pseudo_user and pseudo_user[elm] in potlib[elm]: 
                    pots[i] = pseudo_user[elm]

        # set potential by auto %
        for i,elm in enumerate(elements):
            if pots[i] != None: continue
            if elm not in potlib:
                raise KeyError("No useable POTCAR for %s in the pseudopotential library !" %symbol)
            for tag in ['_3','_2','','_sv','_pv','_d','_s','_h']:
                if elm+tag in potlib[elm]:
                    pots[i] = elm+tag
                    break

        # create potential %
        enmax = []
        enmin = []
        potcar = ''
        for elm,pot in zip(elements,pots):
            # read potcar %
            with open(potlib[elm][pot],'r') as f: 
                lines = f.readlines()
            potcar += ''.join(lines)  
            # search enmax %
            for line in lines:
                if 'ENMAX' in line:
                    enmax.extend(re.findall(r'ENMAX\s*=\s*(\d+\.\d+)',line))
                    enmin.extend(re.findall(r'ENMIN\s*=\s*(\d+\.\d+)',line))
                    break

        if stdout != None:
            self.write_potcar(potcar, stdout)	 
        enmax = np.array(enmax,dtype=float).max()
        enmin = np.array(enmin,dtype=float).min()

        return enmax,enmin

    def set_kpoints(self, stdout, kwargs):
        """
        """

        kpoints = {}
        if 'kspacing' in kwargs:
            pass
        elif self.model == 'kspacing':
            kpoints = {'kspacing':self.kpoints}
        else:
            self.write_kpoints(stdout) 
        
        return kpoints 

    def set_vdw(self, elements, stdout):
        """
        """
        if hasattr(self,"vdw"):
            if self.vdw in ['B86', 'B88', 'DF2', 'rDF2', 'rPBE','optPBE', 'rVV10']:

                self.write_kernel(stdout)
                params = self.vdw_parameters(elements)
                return Incar('vdw', params)

        return  {}

    def set_incar(self, incar, stdout):

        # update params encut %
        enmax, enmin = incar.encut
        if 'encut' not in incar:
            if self.cutoff >= enmin:
                incar['encut'] = self.cutoff  
            else:
                incar['encut'] = min(round(self.cutoff*enmax,4),520)	

        # update default %        
        incar.downdate(self.tasks.base) 

        # inherits first if spin calculation %
        if self.get_spin(incar) is True:
            # set lwave and lcharg%
            if 'lwave' not in incar :
                incar['lwave'] = False

            # set magmom if calculation without input and wavecar%
            if 'icharg' not in incar or incar['icharg'] < 10:
                if 'magmom' not in incar:
                    incar.update(self.get_magnetic(incar))

        self.write_incar(incar, stdout)		

        return incar
           
    @property
    def potential(self):
        return self.__pot 

    @potential.setter
    def potential(self, value:Union[str,tuple]):
        from os.path import abspath, exists, expanduser

        pots = {}
        if isinstance(value, str):
            path = value
        else:
            path,pots = value
 
        if '~' in path: path = expanduser(path)
        if not exists(path):
            raise IOError ('invalid input VASP pseudo potential directory')
        self.__pot = (abspath(path), pots) if len(pots) else abspath(path)

    @property 
    def program(self):
        return self.__program 

    @property
    def external_files(self):
        return self.__files

    @property
    def optcell(self):
        return self.__optcell

    @program.setter
    def program(self, value=None):
        from os.path import isfile
        if isinstance(value,str) and isfile(value):
            self.__program = value 
        elif isinstance(value, dict):
            self.__program = value
        else:
            raise IOError ('invalid input VASP program')

    @external_files.setter
    def external_files(self,value):
        from os.path import exists,abspath
        import warnings
        if isinstance(value,str) and exists(value):
            self.__files.add(abspath(value))
        elif isinstance(value,(tuple,list)):
            for path in value:
                if exists(path):
                    self.__files.add(abspath(path))
                else:
                    warnings.warn("No external file: %s" %path)
        else:
            raise ValueError("Unsupported input formats for vasp.external_files !")
       	
    @optcell.setter
    def optcell(self,value):
        """
        set OPTCELL
        vasp.optcell = 110 or '110' or 'xy' or 1,1,0
            type = str, int, tuple
        You can insert any delimiter when entering a string
        """
        import numpy as np
        axis = []
        optc = []
        if isinstance(value,int) and len(str(value)) == 3:
            self.__optcell = ''.join(list(str(value)))

        elif isinstance(value,str) or isinstance(value,tuple):
            for i in value:
                if i.isdigit(): optc.append(i)
                elif i.isalpha(): axis.append(i.lower())

            if len(axis) == 0:
                assert len(optc) == 3
                self.__optcell = ''.join(optc)
            else:
                optc = ['0','0','0']
                if 'x' in axis: optc[0] = '1'
                if 'y' in axis: optc[1] = '1'
                if 'z' in axis: optc[2] = '1'
                self.__optcell = ''.join(optc)

        elif isinstance(value,(list,np.ndarray)) and len(value) == 3:
            self.__optcell = '{0[0]:d}{0[1]:d}{0[2]:d}'.format(value) 


    def get_spin(self,incar):
        '''
        is ispin=2 or lsorbit=True % 
        '''
       	spin = False 
        # magnetic property % 
        if 'lsorbit' in incar and incar['lsorbit'] == True:
            spin = True
        elif 'ispin' in incar and incar['ispin'] == 2:
            spin = True

        return spin

    def get_magnetic(self, lsorbit=False, **kwargs):
        # input %
        if 'extra' in self.tasks and 'magmom' in self.tasks.extra:
            if self.tasks.extra['magmom'] != None:
                return {'magmom':self.tasks.extra['magmom']}
        # auto %
        natom = sum(self.structure.number_of_atoms)
        if lsorbit:
            natom = 3 * natom

        return {'magmom':'%d*1' %natom}
