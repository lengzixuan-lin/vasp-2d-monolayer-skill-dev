import os
import numpy as np
from jamip.analysis.base import FinderSet


class __Vasptools(FinderSet):

    __function__ = ['potcar', 'phonon', 'bond', 'standard', 'backup', 'clean','kpath']

    def __init__(self,*args,**kwargs):
        self.syspath = set()
        self.sysfile = set()

    def load_pool(self,poolfile):
        from os.path import join,isdir,isfile,dirname,abspath
        if isfile(poolfile):
            import pickle
            try:
                root = abspath(dirname(poolfile))
                with open(poolfile,'rb') as f:
                    pool=pickle.load(f)
                for dir in pool.keys():
                    if isfile(join(root,dir,'.status')):
                        self.syspath.add(join(root,dir))
            except:
                print('PathError: Invalid poolfile')

        elif isdir(poolfile):
            root = abspath(poolfile)
            if isfile(join(root,'.status')) or isfile(join(root,'POSCAR')):
                self.syspath.add(root)
            else:
                for dir in os.listdir(root):
                    if isfile(join(root,dir,'.status')) or isfile(join(root,dir,'POSCAR')):
                        self.syspath.add(join(root,dir))
                
        else:
            print('PathError: Invalid directory')


    def seek_structure(self):
        '''
        support filetype: poscar, contcar, .xyz, .vasp, .mol, .cif
        '''
        from jamip.structure import read
        structure_set = {}
        # seek from self.files %
        for path,filename in self.files:
            if filename.endswith('.cif'):
                ftype='cif'
            elif filename.endswith('.xyz'):
                ftype='xyz'
            elif filename.endswith('.mol'):
                ftype='mol'
            elif filename.endswith('.vasp'):
                ftype = 'poscar'
            elif 'CONTCAR' in os.path.basename(filename):
                ftype='poscar'
            elif 'POSCAR' in os.path.basename(filename):
                ftype='poscar'
            else:
                continue

            try: 
                file = os.path.join(path,filename)
                structure_set[file] = read(file,ftype)
            except:
                pass

        # try again: seek from self.syspath %
        if len(structure_set) == 0 and len(self.syspath) == 1:
            for filename in os.listdir(list(self.syspath)[0]):
                abspath = os.path.join(list(self.syspath)[0],filename)
                if filename.endswith('.cif'):
                    ftype='cif'
                elif filename.endswith('.xyz'):
                    ftype='xyz'
                elif filename.endswith('.mol'):
                    ftype='mol'
                elif filename.endswith('.vasp'):
                    ftype = 'poscar'
                elif os.path.isfile(abspath) and ('CONTCAR' in filename or 'POSCAR' in filename):
                    ftype='poscar'
                else:
                    continue
                
                try: 
                    structure_set[abspath] = read(abspath,ftype)
                except:
                    pass

        # raise Error % 
        if len(structure_set) == 0:
            raise ValueError("Seek structure files failed.") 

        return structure_set

    def run(self,params,**kwargs):
        ''' main project'''

        tasks = []
        inputs = []

        for i in params['vasp_tools']:
            if i in self.__function__:
                tasks.append(i)
            else:
                inputs.append(i)
        
        if 'pool' in params:
            inputs.append(params['pool'])
        if len(inputs) == 0:
            inputs.append(os.getcwd())

        # initialize path %
        self.stdin = inputs

        # run tasks %
        for task in tasks:
            if task == 'standard':
                self.standard()
            elif task == 'bond':
                self.bonding()
            elif task == 'phonon':
                self.write_force()
            elif task == 'potcar':
                self.write_potcar()
            elif task == 'backup':
                self.backup()
            elif task == 'kpath':
                self.kpath()
            elif task == 'clean':
                self.clean()

    def clean(self):
        from os.path import isfile,join

        def remove(root,files):
            num = 0
            for f in files:
                if f in ['INCAR','POSCAR','POTCAR','OPTCELL','KPOINTS']:
                    continue
                elif '.' in f and f.split('.')[-1] in ['x','py','dat','pbs']:
                    continue
                else:
                    num += 1
                    os.remove(join(root,f))
            return num

        while(True):
            in_content = input("Notice that you are deleting files. Type Y/N to continue: ")
            if in_content.lower()[0] == "y":
                break
            if in_content.lower()[0] == "n":
                return 0
            else:
                print("Invalid input. Please try again.")

        num = 0
        for path in self.syspath:
            if not isfile(join(path,'OUTCAR')) and not isfile(join(path,'.status')): 
                continue
            for root,dirs,files in os.walk(path):
                if 'OUTCAR' in files:
                    num += remove(root,files)
            
        print("clean finished. %s files were deleted" %num)

    def backup(self):
        import shutil

        if len(self.files) == 0:
            raise ValueError("Requires filename as an input parameter.")

        fdict = {}
        for path,filename in self.files:
            if filename not in fdict.keys():
                fdict[filename] = savedir = os.path.join(os.getcwd(),filename.replace('/','_'))
                if not os.path.exists(savedir):
                    os.makedirs(savedir)
            originfile = os.path.join(path,filename)
            copyfile = os.path.join(fdict[filename],os.path.basename(path)) 
            shutil.copyfile(originfile,copyfile)
            
        print("backup finished")

    def standard(self):

        from jamip.abtools.vasp.vaspio import VaspIO
        vaspio = VaspIO()
        # try read all possible structure models %
        structures = self.seek_structure()

        num = 0
        for p,v in structures.items():
            vaspio.write_poscar(v,p)
            num += 1
                
        print("standard successed : %s" %num)

    def kpath(self):
        from jamip.structure import read

        num = 0
        for path in self.structures:
            try:
                self.kprint(path)
                num += 1
            except:
                pass
                
        print("kpath successed : %s" %num)

    def bonding(self):
        from jamip.structure.bonding import Bonding
        from jamip.utils.rwigs import RWIGS,radius
        from jamip.structure import read

        for path in self.structures:
            try:
                structure = read(path)
                d,elms = Bonding(structure, radius=RWIGS).get_minbond()
                if len(elms) == 2: 
                    bond = '{0[0]}-{0[1]}'.format(elms)
                elif len(elms) == 1:
                    bond = '{0[0]}-{0[0]}'.format(elms)
                print(os.path.basename(path),': %s : %.3f' %(bond,d) )
            except:
                pass
            
    def write_force(self):
        from os.path import join,exists
        from jamip.analysis.vasp import PhononFinder
        from phonopy.file_IO import parse_FORCE_SETS

        for path in self.syspath:
            try: 
                pf = PhononFinder(path)
                phonon = pf.get_phonon()
                forces = pf.get_forces()
                filename = join(path,'FORCE_SETS')
                pf.write_forces(phonon,forces,filename)
                print('%s created.' %filename)
            except:
                pass

    def write_potcar(self):

        from jamip.abtools.vasp.utils import VaspPotentials
        from jamip.structure import read
        from os.path import exists,join,isdir,dirname
        from ruamel import yaml
        import shutil

        potenv = os.path.join(os.environ['HOME'],'.jamip','env','pot.yaml')
        priority = ['_3','_2','','_sv','_pv','_d','_s','_h']
        pots = {}
        if os.path.exists(potenv):
            try:
                with open(potenv,'r') as f:
                    pots = yaml.safe_load(f) 
                    if pots == None:
                        pots = {}
            except:
                pass

        if 'vasp' in pots and os.path.exists(pots['vasp']):
            print('Potentials read from %s' %pots['vasp'])
            print('Potentials priority for X: '+' > '.join('X'+i for i in pots['vasp_priority']))
            potdir = pots['vasp']
            priority = pots['vasp_priority']

        else:
            potdir = input('Please input VASP Pseudopotential library path: ')
            if os.path.exists(potdir):
                pots['vasp'] = potdir
                pots['vasp_priority'] = priority
                with open(potenv, 'w') as f:
                    yaml.dump(pots, f, Dumper=yaml.RoundTripDumper,indent=3)
            else:
                raise OSError('Pseudopotential library %s not exists!' %potdir)
            print('Potentials priority for X:  ' + ' > '.join('X'+i for i in priority))

        potlib = VaspPotentials(potdir)

        for path in self.structures:
            try:
                structure = read(path)
                elements = list(structure.species_of_elements)
                potname = []
                potcar = ''
         
                # set potential by auto %
                for elm in elements:
                    pot = None
                    if elm not in potlib:
                        raise KeyError("No useable pseudopotential for %s !" %elm)
                    for tag in priority:
                        if elm+tag in potlib[elm]:
                            potname.append(elm+tag)
                            break
          
                # read potcar %
                for elm,pot in zip(elements,potname):
                    with open(potlib[elm][pot],'r') as f:
                        lines = f.readlines()
                    potcar += ''.join(lines)

                output = join(dirname(path), 'POTCAR')
                if exists(output): 
                    os.rename(output, join(dirname(path), "POTCAR_bak"))
                 
                print('Potential {0} > {1}'.format(' + '.join(potname), path))
                with open(output,'w') as f:
                    f.write(potcar)

            except: 
                pass

    def kprint(self, path):
        from jamip.utils.brillouin_zone import HighSymmetryKpath
        from jamip.abtools.base.kpoints import __KPATH__,__KPT__
        from jamip.structure import read

        structure = read(path)
        bz = HighSymmetryKpath()
        kpoint = bz.get_HSKP(structure.bandStructure())
        kpaths = []
        for points in kpoint['Path']:
            # if add segments into suggest kpath % 
            kpath = []
            for p in points:
                kpath.append(__KPT__(p, kpoint['Kpoints'][p]))
            kpaths.append(kpath)

        kpaths = __KPATH__(kpaths)
        insert = kpaths.insert
        if isinstance(insert, int):
            insert = [insert] * len(kpaths.kpath)
        print(path,' SG: {0}({1})  PG: {2}'.format(bz.spacegroup,bz.sgnum,bz.pointgroup))
        for kpt,num in zip(kpaths.kpath,insert):
            print(' "{0} {1}",'.format(kpt,num))
        

