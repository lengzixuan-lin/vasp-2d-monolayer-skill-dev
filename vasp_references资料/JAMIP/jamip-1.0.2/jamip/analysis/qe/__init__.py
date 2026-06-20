__all__ = ['BandFinder','DosFinder']
from jamip.analysis import Finder
from .qexml import GrepXml
from .band import GrepBand
from .dos import GrepDos
import numpy as np
import re
import os

class DosFinder(Finder,GrepXml,GrepDos):
    
    def __init__(self,stdin=None):
        self.__task__ = 'dos'
        self.stdin = stdin

    @property
    def stdin(self):
        from os.path import exists,join
        if self.__builder__ == 'jamip':
            stdin = join(self._stdin,'qerun','dos.xml')
        elif self.__builder__ == 'qeout':
            stdin = join(self._stdin,'data-file-schema.xml')
        elif self.__builder__ == 'qexml':
            stdin = self._stdin
        return stdin

    @property
    def _tdosdat(self):
        from os.path import exists,join
        if self.__builder__ == 'jamip':
            file1 = join(self._stdin,'qerun','pdos','pdos_tot')
            file2 = join(self._stdin,'qerun','dos.plt.dat')
            if exists(file1): return file1
            elif exists(file2): return file2
            raise OSError("datafile not exists!" )

    @property
    def _pdosdat(self):
        from os.path import isdir,join
        if self.__builder__ == 'jamip':
            path = join(self._stdin,'qerun','pdos')
            if isdir(path):
                return path
        raise OSError("datafile not exists!" )

    @stdin.setter
    def stdin(self,path):
        self._stdin = self.seek(path)

    def get_fermi(self):
        return self.fermi_energy(self.stdin)

    def get_volume(self): 
        if self.__builder__ == 'jamip':
            lattice = GrepXml().lattice(self.stdin)
            rec_lattice = np.linalg.det(lattice*5.29177211/10)
            return rec_lattice

    def get_vbm(self,prec=0.01):
        nelec = GrepXml().nelec(self.stdin)
        tdos = self._get_tdos(self._tdosdat)
        Ecum = np.cumsum(tdos[:,1])*(tdos[1,0]-tdos[0,0])
        for (e,dos),cum in zip(tdos[:,:2], Ecum):
            if nelec-cum < 1e-4 :
                return e

    def get_dos(self):
        from os.path import exists,join
        if self.__builder__ == 'jamip':
            return self.get_tdos()

    def get_tdos(self):
        dos = self._get_tdos(self._tdosdat)
        self._dos_type = 'tdos'
        self.spin = 1
        dos_energy = dos[:,0]
        dos = dos[:,1]
        return dos_energy,dos

    def get_pdos(self):
        from os.path import exists,join
 
        path = self._pdosdat
        self._dos_type = 'pdos'
        self.orbits=['s','p','d']
        self.spin=1
        element = set()
        pdos = {}
 
        for file in os.listdir(path):
            result = re.findall('pdos_atm#\d+\(([A-Z][a-z]?)\)_wfc#\d\(([spd])\)', file)
            if len(result):
                elm, orbit = result[0]
                element.add(elm)
                key = '{}-{}'.format(elm, orbit)
                dos = self._get_tdos(join(path, file))
                if key not in pdos:
                    pdos[key] = dos[:,1]
                else:
                    pdos[key] += dos[:,1]
                 
        dos_energy = dos[:,0]
        tmps = []
        for i in element: 
            tmp = []
            for j in self.orbits:
                key = '{}-{}'.format(elm, j)
                if key in pdos:
                    tmp.append(pdos[key])
                else:
                    tmp.append(np.zeros_like(dos_energy))
            tmps.append(tmp)
 
        pdos = np.array(tmps, dtype=float)
 
        return list(element),dos_energy,pdos

class BandFinder(Finder,GrepBand):

    def __init__(self,stdin=None):
        self.__task__ = 'band'
        self.__kpath__ = None
        self.__insert__ = None
        self.stdin = stdin

    @property
    def stdin(self):
        from os.path import exists,join
        if self.__builder__ == 'jamip':
            stdin = join(self._stdin,'qerun','band.xml')
        elif self.__builder__ == 'qeout':
            stdin = join(self._stdin,'data-file-schema.xml')
        elif self.__builder__ == 'qexml':
            stdin = self._stdin
        return stdin

    @stdin.setter
    def stdin(self,path):
        self._stdin = self.seek(path)

    @property
    def kpath(self):
        if self.__kpath__ != None:
            return self.__kpath__

        if self.__builder__ == 'jamip':
            stdin = os.path.join(self._stdin,'qerun','band.in')
            self.__kpath__, self.__insert__ = self._get_kpath(stdin)

        return self.__kpath__

    @property
    def insert(self):
        return self.__insert__ 

    def get_rec_lattice(self):
        if self.__builder__ == 'jamip':
            lattice = GrepXml().lattice(self.stdin)
            rec_lattice = np.linalg.inv(lattice*5.29177211/10)*2*np.pi
            return rec_lattice

    def get_cbvb(self,bands=None,isdata=False):
        if not isinstance(bands,np.ndarray):
            bands = self.get_bands()
        nelect = GrepXml().nelec(self.stdin)
        filled = int(nelect/2)
        for index in np.arange(filled,bands.shape[1]):
            if max(bands[:,index,1]) < 0.001:
                if isdata:
                    return bands[:,index-1,0],bands[:,index,0]
                else:
                    return index-1,index

    def get_cbmvbm(self,bands=None,kpoints=None):
        if not isinstance(bands,np.ndarray):
            bands = self.get_bands()
        if not isinstance(kpoints,np.ndarray):
            kpoints = self.get_kpoints()
        cbvb = self.get_cbvb(bands=bands)
        vb = bands[:,cbvb[0],0]
        cb = bands[:,cbvb[1],0]
        # cbm %
        cvdict = {
            'vbm': {'index': (cbvb[1],np.argmax(vb)),
                    'energy': np.max(vb),
                    'kpoint': kpoints[np.argmax(vb)]},
            'cbm': {'index': (cbvb[0],np.argmin(cb)),
                    'energy': np.min(cb),
                    'kpoint': kpoints[np.argmin(cb)]},
            'gap': np.round(np.min(cb)-np.max(vb),6)
            }
        return cvdict


    def get_bands(self):
        stdin = self.stdin
        # single %
        return self._get_band(stdin)

    def get_kpoints(self):
        stdin = self.stdin
        # single %
        return self._get_kpoint(stdin)

    def get_fermi(self):
        stdin = self.stdin
        # single %
        return self.fermi_energy(stdin)
