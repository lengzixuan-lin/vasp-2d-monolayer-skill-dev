import os
import django
import warnings
warnings.filterwarnings("ignore")

os.environ['DJANGO_SETTINGS_MODULE']='jamip.db.db.settings'
django.setup()
from .materials.structure import Structure
from .materials.composition import Composition
from .materials.element import Element
from .materials.species import Species
from .materials.atom import Atom
from .materials.entry import Entry
from .materials.spacegroup import Spacegroup
from .materials.prototype import Prototype

from .iostream.read import Read
from .iostream.write import Write

from .modeling.structureFactory import StructureFactory
from jamip.analysis.vasp import *
import pandas as pd

class Connect(object):

    def __init__(self):
        self.__entry = 'vasp'

    def load_structure(self,path=None):
        '''
        support filetype: poscar, contcar, .xyz, .vasp, .mol, .cif
        '''
        from os.path import join, exists, isdir, isfile
        
        files = []
        if path == None:
            files = os.listdir(os.getcwd())

        elif isinstance(path,str):
            if isfile(path):
                files.append(path)
            elif isdir(path):
                for file in os.listdir(path):
                    files.append(join(path,file))
            else:
                raise OSError("PATH %s not exists!" %path)

        elif isinstance(path, Iterable):
            for i in path:
                if isfile(i):
                    files.append(i)
            if len(files) == 0: 
                raise ValueError("Unkown path type!")

        else:
            raise ValueError("Unkown path type!")

        # seek from files %
        for filename in files:
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
                raw=Read(os.path.join(path,filename), ftype).run()
                Structure().create(raw, isPersist=True)
                print(filename)
            except:
                pass

    def load_entry(self, path=None, properties=None):
        from os.path import join, exists, isdir, isfile

        dirs = []
        if path == None:
            path = os.getcwd()

        if isdir(path):  # calculation directory %
            if exists(join(path,'.status')):
                dirs.append(path)
            elif exists(join(path,'OUTCAR')):
                dirs.append(path)
            else:
                for dir in os.listdir(path):
                    if exists(join(path,dir,'.status')):
                        dirs.append(path)

        elif isfile(path): # task pool file %
            import pickle
            try:
                root = dirname(path)
                with open(value,'rb') as f:
                    pool=pickle.load(f)
                for dir in pool.keys():
                    if exists(join(root, dir, '.status')):
                        dirs.append(join(root, dir))
            except:
                raise OSError('Invalid poolfile !')
                
        if len(dirs) == 0:
            print('No Valid calculation directory !')
        else:
            sum = 0
            for path in dirs:  
                EntryBuilder().load(path,properties,isPersist=True)
                sum += 1
            print('Total = %d' %sum)

class EntryBuilder(object):

    cal_params = ['date','datetime','vasp_version','prec','ediff','ediffg']

    def __init__(self,name='',path=None):
        self.entry = Entry()
        self.entry.name = name
        self.entry.path = path

    def load(self, root, properties=None, isPersist=False):
        from os.path import join, exists, basename, realpath
        from jamip.abtools.vasp.check import CheckStatus
        from jamip.analysis.vasp import Finder

        if len(self.entry.name) == 0:
            self.entry.name = basename(root)
            self.entry.path = realpath(root)

        vasp = Finder(root)

        # load scf structure %
        raw = Read(vasp.stdcell, dtype='vasp').run()
        self.entry.structure = Structure().create(raw, isPersist)

        # load properties %
        if properties == None:
            properties = [field.name for field in self.entry._meta.fields]
        print(properties)

        # calculated_parameters
        if 'calculated_parameters' in properties:
            cal_params = {}
            for key in self.cal_params:
                try:
                    cal_params[key] = vasp.grep(key)
                except:
                    cal_params[key] = None
            self.entry.calculated_parameters = cal_params

        # free_energy
        if 'energy' in properties:
            self.set_energy(vasp.stdscf)

        if 'bandgap' in properties:
            self.set_bandgap(root)

        if 'boltztrap' in properties:
            self.set_boltztrap(root)

        if 'effective_mass_of_bandside' in properties:
            self.set_emass(root)

        if 'born_effective_charge' in properties:
            self.set_born_charge(root)

        self.entry.save()

    def set_born_charge(self,root):
        path = os.path.join(root,'electric','born')
        if not os.path.exists(path): return 0
        from jamip.analysis.vasp.outcar import GrepOutcar 
        try:
            self.entry.born_effective_charge = {}
            for i,array in enumerate(GrepOutcar().born(path)):
                self.entry.born_effective_charge[i] = array
        except:
            print('load born_charge error')

    def set_boltztrap(self, root):
        path = os.path.join(root,'electric','boltztrap','boltztrap.dat')
        if not os.path.exists(path): return 0
        try:
            with open(path,'r') as f:
                lines = f.readlines()
            assert lines[5].split()[-1] == "e_mass"
            assert lines[6].split()[-1] == "H_mass"
      
            emass = {'emass': lines[5].split()[0],
                     'hmass': lines[6].split()[0]}
            self.entry.effective_mass_of_bandside = emass
        except:
            print('load boltztrap error')

    def set_emass(self,root):
        try:
            emass = BandFinder(root).get_emass()
            emass_dict = {}
            cbm,vbm = [],[]
            for key,mass in emass.items():
                if 'cbm' in key:
                    cbm.append(mass)
                if 'vbm' in key:
                    vbm.append(mass)
            if len(cbm):
                emass_dict['hmass'] = round(len(cbm)/sum([1/i for i in cbm]),4)
            if len(vbm):
                emass_dict['emass'] = round(len(vbm)/sum([1/i for i in vbm]),4)
            self.entry.effective_mass_of_bandside = emass_dict 
        except:
            print('load emass error')
        
    def set_bandgap(self,root):
        try:
            self.entry.bandgap = BandFinder(root).get_bandgap()
        except:
            print('load bandgap error')

    def set_energy(self,path):
        from jamip.analysis.vasp.outcar import GrepOutcar
        try:
            free_energy = GrepOutcar().free_energy(path)
            self.entry.energy = free_energy
            if self.entry.structure is not None:
                self.entry.energy_per_formula = free_energy/self.entry.structure.multiple
                self.entry.energy_per_atom = free_energy/self.entry.structure.natoms
        except:
            print('load energy error')
            


class SqliteSQL:

    __db__ = 'sqlite3'

    def __init__(self):
        pass

    def sql_by_id(self,table,mainkey=''):
        dataset = pd.DataFrame(columns=['name','format','natoms','SG'])
        if table == 'entry':
            fields = [f.attname for f in Entry._meta.fields]
            if mainkey == '':
                query = Entry.objects.all()
            else:
                query = Entry.objects.filter(name=mainkey)
                mainkey = ' for %s' %mainkey
                
            if len(query) == 0:
                print('Query failed%s in table %s. Exit!' %(mainkey,table))
                return
            #print(query[0].calculated_parameters)
            dataset.loc[0] = [query[0].name,
                              query[0].structure.composition.formula,
                              query[0].structure.natoms,
                              query[0].structure.spacegroup]
            print(dataset)
        while True:
            line = input("([fileds]/all/none):")
            if line == 'all':
                print(fields)
            elif len(line):
                for key in line.split():
                    try:
                        result = getattr(query[0],key)
                        if isinstance(result,dict):
                            for k,v in result.items():
                                dataset[k] = v
                        else:
                            dataset[key] = result 
                    except:
                        pass
                print(dataset)
            else:
                return 

    def load_history(self):
        return self.sql_by_id(table='entry')

class __DBShell(Connect,SqliteSQL):

    def __init__(self, params=None, *args, **kwargs):
        super().__init__()
        path = None
        if 'pool' in params:
            path = os.path.abspath(params['pool']) 
        
        if params['db']  == 'structure':
            self.load_structure(path)
        elif params['db'] == 'entry':
            self.load_entry(path)
        elif params['db'] == 'history':
            self.load_history()

