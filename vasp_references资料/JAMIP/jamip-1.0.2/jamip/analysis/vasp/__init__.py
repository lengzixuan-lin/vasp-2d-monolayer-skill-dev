import os
import re
import numpy as np
from jamip.analysis import Finder
from .outcar import GrepOutcar
from .band import GrepBand,GrepProcar,Kpath
from .dos import GrepDos
from .optics import GrepOptics
from os.path import exists,join

class BandFinder(Finder,Kpath,GrepBand):

    __multi__ = None

    def __init__(self,stdin=None):
        self.__task__ = 'band'
        self.stdin = stdin

    @property
    def stdin(self):

        if self.__builder__ == 'jamip':
            stdin = join(self._stdin,'electric','band')
            if exists(join(stdin,'OUTCAR')):
                self.__multi__ = False
                return stdin

        elif self.__builder__ == 'vasp':
            stdin = self._stdin
            if exists(join(stdin,'OUTCAR')):
                self.__multi__ = False
                return stdin
        else:
            raise RuntimeError('Invaild module builder.')

        banddir = []
        for dir in os.listdir(stdin):
            if '-' in dir and exists(join(stdin,dir,'OUTCAR')):
                banddir.append(dir)
        if len(banddir):
            self.__multi__ = stdin
            return banddir
        else:
            raise IOError("Band calculation files not exists!") 
            
    @stdin.setter
    def stdin(self,path):
        self._stdin = self.seek(path)

    @property
    def kpath(self):
        if self.__kpath__ != None:
            return self.__kpath__

        stdin = self.stdin
        if self.__multi__:
            try:
                from jamip.structure import read
                spath = join(self.__multi__,stdin[0],'CONTCAR')
                self.set_kpath_by_auto(read(spath),stdin)
            except:
                self.set_kpath_by_sub(stdin)
        else:
            self.set_kpath_by_kpoints(stdin)

        return self.__kpath__

    @kpath.setter
    def kpath(self,value):
        if isinstance(value,(list,tuple)):
            if type(value[0]) == str: value=[value]
            self.__kpath__ = value
            stdin = self.stdin
            if self.__multi__:
                for kpts in value:
                    for i in range(len(kpts)-1):
                        A_B = kpts[i].strip('\\')+'-'+kpts[i+1].strip('\\')
                        if A_B not in stdin:
                            raise IOError('Band %s not exists!' %A_B)
        else:
            raise ValueError('Kpath should be list or tuple!')

    def get_bands(self):
        stdin = self.stdin
        # single %
        if self.__multi__ == False:
            return self._get_band(stdin)
        # mutil %
        bands = []
        for k in self.kpath:
            for i in range(len(k)-1):
                dirname = k[i].lstrip('\\')+'-'+k[i+1].lstrip('\\')
                path = join(self.__multi__,dirname)
                bands.append(self._get_band(path))
        shape = bands[0].shape
        bands = np.stack(bands,axis=1).reshape(shape[0],-1,shape[2],shape[3])
        return bands

    def get_kpoints(self):
        stdin = self.stdin
        # single %
        if self.__multi__ == False:
            return self._get_kpoint(stdin)
        # mutil %
        kpoints = []
        for k in self.kpath:
            for i in range(len(k)-1):
                dirname = k[i].lstrip('\\')+'-'+k[i+1].lstrip('\\')
                path = join(self.__multi__,dirname)
                kpoints.append(self._get_kpoint(path))
        return np.array(kpoints).reshape(-1,3)         

    def get_fermi(self,func=max):
        stdin = self.stdin
        # single %
        if self.__multi__ == False:
            return self.fermi_energy(stdin)
        # mutil %
        efermi = []
        for k in self.kpath:
            for i in range(len(k)-1):
                dirname = k[i].lstrip('\\')+'-'+k[i+1].lstrip('\\')
                path = join(self.__multi__,dirname)
                efermi.append(self.fermi_energy(path))
        return func(efermi)

    def get_locpot(self, path=None, axis='z'):
        if path==None: path=self.stdscf
        locpot = self.locpot(path,axis)
        vaccum_level = locpot[0]
        return vaccum_level 
            
    def get_cbvb(self,bands=None,isdata=False):
        if not isinstance(bands,np.ndarray):
            bands = self.get_bands()
        nelect = self.get_info('nelect')
        lsorbit = self.get_info('lsorbit')
        filled = nelect if lsorbit else nelect // 2
        cbvbs = []                                                      
        for spin in bands:                                       
            for index in np.arange(filled,spin.shape[1]):        
                if max(spin[:,index,1]) < 0.001:                 
                    if isdata:
                        cbvbs.append([spin[:,index-1,0],spin[:,index,0]])
                    else:
                        cbvbs.append([index-1,index])
                    break                                               
        return cbvbs 

    def get_bandgap(self,bands=None):
        if not isinstance(bands,np.ndarray):
            bands = self.get_bands()
        cbvbs = self.get_cbvb(bands=bands)
        for cbvb,spin in zip(cbvbs,bands):
            vb = spin[:,cbvb[0],0]
            cb = spin[:,cbvb[1],0]
            gap = {'indirect': np.around(np.min(cb)-np.max(vb),4),
                   'direct'  : np.around(np.min(cb-vb),4)}
            return gap

    def get_cbmvbm(self,bands=None,kpoints=None,path=None):
        if path != None:
            bands = self._get_band(path)
            kpoints = self._get_kpoint(path)
        else:
            if not isinstance(bands,np.ndarray):
                bands = self.get_bands()
            if not isinstance(kpoints,np.ndarray):
                kpoints = self.get_kpoints()
        cbvbs = self.get_cbvb(bands=bands)
        for cbvb,spin in zip(cbvbs,bands):
            vb = spin[:,cbvb[0],0]
            cb = spin[:,cbvb[1],0]
            # cbm %
            cvdict = {
                'vbm': {'index': (cbvb[0],np.argmax(vb)),
                        'energy': np.max(vb),
                        'kpoint': kpoints[np.argmax(vb)]},
                'cbm': {'index': (cbvb[1],np.argmin(cb)),
                        'energy': np.min(cb),
                        'kpoint': kpoints[np.argmin(cb)]},
                }
            cvdict['gap'] = np.round(np.min(cb)-np.max(vb),6) 
            return cvdict

    def get_emass(self,path=None,fit_range=3):

        if path != None: 
            if not exists(join(path,'OUTCAR')):
                raise OSError("Invaild calculation path!")
        elif self.__builder__ == 'vasp' and self.__multi__ == False:
            path = self._stdin

        emass = {}                                                      
        if path != None:
            bands = self._get_band(path)
            kpoints = self._get_kpoint(path)                            
            cbmvbm = self.get_cbmvbm(bands,kpoints)                    
            emass = self._get_emass(bands,kpoints,fit_range=fit_range)      
            return emass

        elif self.__builder__ == "jamip":
            scfdir = join(self._stdin,'scf')
            emassdir = join(self._stdin,'electric','emass')
            rec_vector = self.reciprocal_lattice_vectors(scfdir)

            if exists(emassdir):
                for dir in os.listdir(emassdir):                           
                    path = join(emassdir,dir)                
                    bands = self._get_band(path)
                    kpoints = self._get_kpoint(path)                            
                    # axis: x,y,z ; bd: [cbm,vbm]                             
                    axis = dir.split('-')[0]                                    
                    bd = dir.split('-')[1:]                                   
                    emass.update(self._get_emass(bands,kpoints,rec_vector,axis,bd,fit_range))

        if len(emass) == 0:
            raise IOError("Emass calculation files not exists!") 
        return emass

    def get_insert(self):
        stdin = self.stdin
        # mutil %
        if self.__multi__:
            stdin = join(self.__multi__,stdin[0])
            return Finder(stdin).grep('nkpts')
        else:
            return self._get_band_insert(stdin) 
        

    def get_info(self,func):
        stdin = self.stdin
        # mutil %
        if self.__multi__:
            stdin = join(self.__multi__,stdin[0])

        return Finder(stdin).grep(func)

class ProFinder(BandFinder,Kpath,GrepProcar):

    __multi__ = None

    def __init__(self,stdin=None):
        self.__task__ = 'band'
        self.stdin = stdin

    def get_procar(self):
        stdin = self.stdin
        # single %
        if self.__multi__ == False:
            return self._get_procar(stdin)
        # mutil %
        procars = []
        for k in self.kpath:
            for i in range(len(k)-1):
                dirname = k[i].lstrip('\\')+'-'+k[i+1].lstrip('\\')
                path = join(self.__multi__,dirname)
                procars.append(self._get_procar(path))
        shape = procars[0].shape
        procars = np.stack(procars,axis=1).reshape(shape[0],-1,shape[2],shape[3], shape[4])
        return procars


    def get_tot_procar(self):
        procar = self.get_procar()
        return procar[...,-1,-1]

    def get_emax_procar(self):
        procar = self.get_procar()
        tot_procar = procar[...,-1,-1]
        nm = np.max(tot_procar)
        atominfo = self.get_info('atominfo')
        tmp = 0
        data = []
        labels = []
        info = np.zeros(procar.shape[:3])
        value = np.zeros(procar.shape[:3])
        for atom,num in atominfo:
            # total %
            data.append(np.sum(procar[...,tmp:tmp+num,-1],axis=3))
            labels.append(atom)
            tmp+=num
        data = np.stack(data,axis=3)

        for i in range(procar.shape[0]):
            for j in range(procar.shape[1]):
                for k in range(procar.shape[2]):
                    value[i][j][k] = np.max(data[i,j,k])/nm
                    info[i][j][k] = np.argmax(data[i,j,k])

        return value,info,labels

    def get_pmax_procar(self):
        procar = self.get_procar()
        tot_procar = procar[...,-1,-1]
        nm = np.max(tot_procar)
        atominfo = self.get_info('atominfo')
        tmp = 0
        data = []
        labels = []
        info = np.zeros(procar.shape[:3])
        value = np.zeros(procar.shape[:3])
        for atom,num in atominfo:
            # s obrit %
            data.append(np.sum(procar[...,tmp:tmp+num,0],axis=3))
            labels.append(atom+'-s')
            # p obrit %
            data.append(np.sum(procar[...,tmp:tmp+num,1:4],axis=(3,4)))
            labels.append(atom+'-p')
            # d obrit %
            data.append(np.sum(procar[...,tmp:tmp+num,4:9],axis=(3,4)))
            labels.append(atom+'-d')
            tmp += num
        data = np.stack(data,axis=3)

        for i in range(procar.shape[0]):
            for j in range(procar.shape[1]):
                for k in range(procar.shape[2]):
                    value[i][j][k] = np.max(data[i,j,k])/nm
                    info[i][j][k] = np.argmax(data[i,j,k])

        info = info.astype(int)
        return value,info,labels

class DosFinder(Finder,GrepDos):

    _dos_type = None
    spin = None

    def __init__(self,stdin=None):
        self.__task__ = 'optics'
        self.stdin = stdin

    @property
    def stdin(self):
        if self.__builder__ == 'jamip':
            stdin = join(self._stdin,'electric','dos')
        elif self.__builder__ == 'vasp':
            stdin = self._stdin
        return stdin

    @stdin.setter
    def stdin(self,path):
        self._stdin = self.seek(path)

    def get_fermi(self):
        return self.fermi_energy(self.stdin)

    def get_vbm(self,prec=0.01):
        tdos = self._get_tdos(self.stdin)
        nelect = self.nelect(self.stdin)

        if tdos.shape[-1] == 5:
            tot = tdos[:,3] + tdos[:,4]
        elif tdos.shape[-1] == 3:
            tot = tdos[:,2]

        for energy,tot in zip(tdos[:,0], tot):
            if nelect-tot <= 1e-3:
                return energy

    def get_dos(self):
        import warnings
        try:
            return self.get_pdos()
        except IOError:
            Warnings.warn("DOS data not exists, try to read total DOS...")
            return self.get_tdos()

    def get_tdos(self):

        dos = self._get_tdos(self.stdin)
        if dos.shape[-1] == 3:
            self._dos_type = 'tdos'
            self.spin = 1
            dos_energy = dos[:,0]
            dos = dos[:,1]
        else:
            self._dos_type = 'tdos-ispin'
            self.spin = 2
            dos_energy = dos[:,0]
            dos_up = dos[:,1]
            dos_down = dos[:,2]
            dos = np.stack((dos_up,dos_down),axis=1)
        return dos_energy,dos

    def get_ldos(self):
        dos=self._get_pdos(self.stdin)
        if dos.size == 0:
            raise IOError("DOS data not exists. Did you set the parameter LORBIT ?")

        # normal pdos %
        dos_energy = dos[0,:,0]
        dos_shape = dos.shape[-1]
        self.orbits=['s','p','d']
        if dos_shape == 4:
            # energy s p d
            self._dos_type = 'ldos'
            self.spin = 1
            dos_s = dos[:,:,1]
            dos_p = dos[:,:,2]
            dos_d = dos[:,:,3]
            dos = np.stack((dos_s,dos_p,dos_d),axis=1)
        elif dos_shape == 10:
            # energy s p_y p_z p_x d_xy d_yz d_z2-r2 d_xz d_x2-y2
            self._dos_type = 'pdos'
            self.spin = 1
            dos_s = dos[:,:,1]
            dos_p = np.sum(dos[:,:,2:5],axis=2)
            dos_d = np.sum(dos[:,:,5:],axis=2)
            dos = np.stack((dos_s,dos_p,dos_d),axis=1)
        elif dos_shape == 7:
            # energy s_up s_down p_up p_down d_up d_down
            self.dostype = 'ldos-ispin'
            self.spin = 2
            dos_s = dos[:,:,1]
            dos_p = dos[:,:,3]
            dos_d = dos[:,:,5]
            dos_up = np.stack((dos_s,dos_p,dos_d),axis=1)
            dos_s = dos[:,:,2]
            dos_p = dos[:,:,4]
            dos_d = dos[:,:,6]
            dos_down = np.stack((dos_s,dos_p,dos_d),axis=1)*-1
            dos = np.stack((dos_up,dos_down),axis=1)
        elif dos_shape == 19:
            # energy s*2 p*3*2 d*5*2
            self.dostype = 'pdos-ispin'
            self.spin = 2
            dos_s = dos[:,:,1]
            dos_p = np.sum(dos[:,:,(3,5,7)],axis=2)
            dos_d = np.sum(dos[:,:,(9,11,13,15,17)],axis=2)
            dos_up = np.stack((dos_s,dos_p,dos_d),axis=1)
            dos_s = dos[:,:,2]
            dos_p = np.sum(dos[:,:,(4,6,8)],axis=2)
            dos_d = np.sum(dos[:,:,(10,12,14,16,18)],axis=2)
            dos_down = np.stack((dos_s,dos_p,dos_d),axis=1)*-1
            dos = np.stack((dos_up,dos_down),axis=1)
        elif dos_shape == 13:
            # energy s_total s_mx s_my s_mz p_total p_mx p_my p_mz d_total d_mx d_my d_mz
            self.dostype = 'ldos-soc'
            self.spin = 1
            dos_s = dos[:,:,1]
            dos_p = dos[:,:,5]
            dos_d = dos[:,:,9]
            dos = np.stack((dos_s,dos_p,dos_d),axis=1)
        elif dos_shape == 37:
            # energy s*4 p*3*4 d*5*4
            self.dostype = 'pdos-soc'
            self.spin = 1
            dos_s = dos[:,:,1]
            dos_p = np.sum(dos[:,:,(5,9,13)],axis=2)
            dos_d = np.sum(dos[:,:,(17,21,25,29,33)],axis=2)
            dos = np.stack((dos_s,dos_p,dos_d),axis=1)
        else:
            raise ("Unsupport DOSCAR filetype!")
        return dos_energy,dos

class OpticsFinder(Finder,GrepOptics):

    def __init__(self,stdin=None):
        self.__task__ = 'optics'
        self.stdin = stdin

    @property
    def stdin(self):
        if self.__builder__ == 'jamip':
            stdin = join(self._stdin,'optic','optics')
        elif self.__builder__ == 'vasp':
            stdin = self._stdin
        return stdin

    @stdin.setter
    def stdin(self,path):
        self._stdin = self.seek(path)

    def get_slme(self, L):

        imag, real = self.get_dielectric_func_from_outcar()
        alpha_w = self._alpha_w(imag, real)
        alpha_am = self._alpha_am(alpha_w)

        bf = BandFinder(self._stdin)
        bandgap = bf.get_bandgap()
        Eg = bandgap['direct']
        dEg = bandgap['indirect'] - bandgap['direct']

        if isinstance(L, (list,np.ndarray)):
            results = []
            for i in L:
               results.append(self._slme(alpha_am, i, Eg, dEg))
            return results
        elif isinstance(L, float):
            return self._slme(alpha_am, L, Eg, dEg)
        else:
            raise ValueError("Invalid input thickness")

    def get_dielectric_func_from_outcar(self):
        nedos = np.ceil(self.nedos(self.stdin)/10).astype(int)
        imag = self.dielectric_imag(self.stdin,nedos)
        real = self.dielectric_real(self.stdin,nedos)
        return imag,real

    def get_dielectric_func_from_xml(self):
        import xml.etree.cElementTree as ET

        def xml2array(root):
            dim={}
            dim_order=[]
            field = []
            array = []
            shape = []
            for element in root:
                if element.tag == 'dimension':
                    dim[element.text] = 0
                    dim_order.append(element.text)
                if element.tag == 'field':
                    field.append(element.text)
                if element.tag == 'set':
                    for text in element.findall(".//"):
                        if text.tag == 'set':
                            dim[text.attrib['comment'].split()[0]]+=1
                        elif len(text.text.split()) == len(field):
                            array.append(text.text.split())
            product=1
            for i in reversed(dim_order[1:]):
                 shape.append(int(dim[i]/product))
                 product=dim[i]
            shape.extend([-1,len(field)])
            array=np.array(array,dtype=float).reshape(shape)
            return array
        
        clear = True
        imag = real = None
        xmlfile = join(self.stdin,'vasprun.xml')
        for event, elem in ET.iterparse(xmlfile,events=('start','end')):
            if event == 'start':
                if elem.tag == "dielectricfunction":
                    clear = False

            elif event == 'end':
                if elem.tag == "imag":
                    array = elem.findall('./array')[0]
                    imag = xml2array(array)
                    elem.clear()
                elif elem.tag == "real":
                    array = elem.findall('./array')[0]
                    real = xml2array(array)
                    elem.clear()
                elif elem.tag == "dielectricfunction":
                    break

            if clear:
                elem.clear()

        if imag is None or real is None:
            raise RuntimeError("Failed search keyword %s" %keyword)
        return imag,real

    def get_dielectric_const_of_ionic(self,path=None):
        if path == None:
            if self.__builder__ == "jamip":
                path = join(self._stdin,'optic','dielectric')
            else:
                path = self.stdin
        if not exists(path):
            raise IOError('Dielectric path not exists!')
        diel = self.dielectric_ionic(path)
        return np.mean(np.linalg.eig(diel)[0])

    def get_dielectric_const(self,path=None):
        if path == None:
            if self.__builder__ == "jamip":
                path = join(self._stdin,'optic','dielectric')
            else:
                path = self.stdin
        if not exists(path):
            raise IOError('Dielectric path not exists!')
        diel = self.dielectric(path)
        return np.mean(np.linalg.eig(diel)[0])

class OpticFinder(OpticsFinder):
    
    def __init__(self,stdin=None):
        super().__init__(stdin)

class PhononFinder(Finder):

    def __init__(self,stdin=None):
        self.__task__ = 'phonon'
        self.stdin = stdin

    @property
    def stdin(self):
        return self._stdin

    @stdin.setter
    def stdin(self,path):
        self._stdin = self.seek(path)
        if self.__builder__ != 'jamip':
            raise OSError("Unsupport stdin!")

    def get_softmode_result(self):
        import xml.etree.cElementTree as ET
        path = join(self.stdin,'phonon','softmode')
        data = {}
        for dir in os.listdir(path):
            if not dir.startswith('mode'): continue
            stdin = join(path, dir)
            data[dir] = GrepOutcar().free_energy(stdin)

        return data

    def get_phonon(self):
        from phonopy import Phonopy
        path = join(self.stdin,'phonon','force','mode0','CONTCAR')
        unitcell = self.get_unitcell()
        supercell = self.get_unitcell(path)
        dim = [np.rint(np.linalg.norm(i)/np.linalg.norm(j)).astype(int) for i,j in zip(supercell.cell,unitcell.cell)]
        phonon = Phonopy(unitcell,dim)
        phonon.generate_displacements()
        return phonon

    def get_gruneisen(self, overwrite=False):
        from phonopy import Phonopy, PhonopyGruneisen, load
        # orig %
        phonons = {}
        phonon = self.get_phonon()
        dim = phonon.supercell_matrix
        cellfile = join(self.stdin,'scf','CONTCAR')
        forcefile = join(self.stdin, 'FORCE_SETS')
        if overwrite is True or not exists(forcefile):
            forces = self.get_forces()
            self.write_forces(phonon, forces, forcefile)
        phonons['orig'] = load(
            supercell_matrix=dim,
            #primitive_matrix=None,
            #calculator=interface_mode,
            unitcell_filename=cellfile,
            force_sets_filename=forcefile,
            #born_filename=bornfile,
            symprec=1e-5)

        for scale in ['plus','minus']:
            cellfile = join(self.stdin,'phonon','gruneisen',scale,'relax','CONTCAR')
            forcefile = join(self.stdin, 'phonon', 'gruneisen', scale, 'force', 'FORCE_SETS')
            if overwrite is True or not exists(forcefile):
                unitcell = self.get_unitcell(cellfile)
                phonon = Phonopy(unitcell, dim)
                phonon.generate_displacements()
                forces = self.get_forces(scale)
                self.write_forces(phonon, forces, forcefile)
            # add %
            phonons[scale] = load(
                supercell_matrix=dim,
                unitcell_filename=cellfile,
                force_sets_filename=forcefile,
                symprec=1e-5)

        gruneisen = PhonopyGruneisen(phonons['orig'],phonons['plus'],phonons['minus'])

        return gruneisen

    def get_unitcell(self, path=None):
        from phonopy.interface.vasp import read_vasp
        if path == None:
            path = join(self.stdin,'scf','CONTCAR')
        if exists(path):
            return read_vasp(path)
        else:
            raise OSError('%s not exists!' %path)

    @classmethod
    def write_forces(self,phonon,force,filename):
        from phonopy.file_IO import write_FORCE_SETS
        phonon.set_forces(force)
        dataset = phonon.displacement_dataset
        write_FORCE_SETS(dataset,filename=filename)

    def get_forces(self,scale=''):
        # set path %
        if scale:
            path = join(self.stdin,'phonon','gruneisen',scale,'force')
        else:
            path = join(self.stdin,'phonon','force')
        return self._get_forces(path)

    @classmethod
    def _get_forces(self,path):
        import xml.etree.cElementTree as ET

        def xml2varray(root):
            varray = []
            for i in root:
                varray.append(i.text.split())
            return varray

        forces = []
        for dir in np.sort(os.listdir(path)):
            if not dir.startswith('mode'): continue
            xmlfile = join(path,dir,'vasprun.xml')
            clear = True
            for event, elem in ET.iterparse(xmlfile,events=('start','end')):
                if event == 'start':
                    if elem.tag == "varray":
                        clear = False
         
                elif event == 'end':
                    if elem.get('name') == "forces":
                        forces.append(xml2varray(elem))
                        elem.clear()
                        break
         
                if clear:
                    elem.clear()

        forces = np.array(forces,dtype=float)
        return forces
          

class VaspFinder(Finder):

    __task__ = ['band','dos','optic']

    def __new__(cls,task,stdin):

        if task == 'band':
            newcls = BandFinder
        else:
            raise Keyerror("Unsupport task type %s" %value)

        Finder.seek(newcls,stdin)
        newcls.__task__ = task
        return super().__new__(newcls)

if __name__ == "__main__":
    vf = VaspFinder('band')

