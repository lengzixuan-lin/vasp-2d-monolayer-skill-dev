from .outcar import GrepOutcar
import numpy as np
import os
import re

class Kpath:

    __kpath__ = None

    def _get_band_insert(self,path):
        with open(os.path.join(path,'KPOINTS')) as f:
            f.readline()   
            band_insert = int(f.readline())
        return band_insert

    def set_kpath_by_kpoints(self,path):
        '''
        input :
            path: get kpath from KPOINTS.

        '''
        with open(os.path.join(path,'KPOINTS')) as f:
            f.readline()   
            nkpt = int(f.readline())
            model = f.readline().strip()
            if model.startswith(('L','l')):
                kpath = []
                for i in f:
                    kpoint = re.findall(r"[-]?\d\.\d+",i.split('!')[0])
                    if len(kpoint) == 3 and '#' not in i.split('!')[0]:
                        kpath.append(re.sub('\W+','',i.split('!')[1]))
            else:
                raise OSError('KPOINTS mpdel should be Line Model, not %s !' %model)

        assert (len(kpath) & 1) == 0
        kpath_total = []
        kpath_part = [kpath[0]]
        for i,k in enumerate(kpath[1::2],1):
            if len(kpath) == 2*i:
                kpath_part.append(k)
                kpath_total.append(kpath_part)
            elif k == kpath[2*i]:
                kpath_part.append(k)
            else: 
                kpath_part.append(k)           
                kpath_total.append(kpath_part)     
                kpath_part = [kpath[2*i]]
        self.__kpath__ = kpath_total

    def set_kpath_by_auto(self,structure,banddir):
        '''
        input :
            structure: seek kpath by structure symmetry.
            banddir: a reference for whether seek path was calculated.

        '''
        from jamip.utils.brillouin_zone import HighSymmetryKpath
        cell = structure.bandStructure()
        kpoint = HighSymmetryKpath().get_HSKP(cell)
        for i,kpts in enumerate(kpoint['Path']):
            for j in range(len(kpts)-1):
                A_B = kpts[j].strip('\\')+'-'+kpts[j+1].strip('\\')
                if A_B not in banddir:
                    return self.set_kpath(self.banddir)
                else:
                    banddir.remove(A_B)
            if len(banddir) == 0:
                break
        self.__kpath__ = kpoint['Path'][:i+1]

    def set_kpath_by_sub(self,band):
        ''' 
        input :
            band: band paths in segments, list, for instance,  
                  ['Gamma-X','X-U','U-R','R-Gamma']

        @properiy :
            self._kpath = [['Gamma','X','U','R','Gamma']]
        
        Warning! The final band path may not be consistent with 
        the initial setting!   
        '''
        # search next %
        def head(k,band):
            knext=[]
            bandn=[]
            bandpop=[]
            for d in band:
                if re.search('^%s-'%k,d):
                    knext.append(d.split('-')[1])
                    bandpop.append(d)
                else:
                    bandn.append(d)
            if len(knext) == 1:
                return knext[0],bandn
            else:
                return None,band
        # search last %
        def tail(k,band):
            klast=[]
            bandn=[]
            for d in band:
                if re.search('-%s$'%k,d):
                    klast.append(d.split('-')[0])
                else:
                    bandn.append(d)
            if len(klast) == 1:
                return klast[0],bandn
            else:
                return None,band
        sort_kpath=[]
        while len(band):
            init = band.pop(-1)
            kpath = init.split('-')
            klen = len(band)
            while klen:
                # search next %
                knext,band = head(kpath[-1],band)
                if knext:
                    kpath.append(knext)
                # search last %
                klast,band = tail(kpath[0],band)
                if klast:
                    kpath.insert(0,klast)
                if len(band) == klen:
                    break
                else:
                    klen=len(band)
            sort_kpath.append(kpath)
        klen = [len(k) for k in sort_kpath] 
        kklen = len(klen)
        sorted_kpath=[]
        while kklen > 1:
            kid = np.argsort(klen)[-1]
            init = sort_kpath[kid]
            for k in np.argsort(klen)[::-1][1:]:
                if sort_kpath[k][0] == init[-1]:
                    sort_kpath[kid].extend(sort_kpath.pop(k)[1:])
                    break
                if sort_kpath[k][-1] == init[0]:
                    sort_kpath[k].extend(sort_kpath.pop(kid)[1:])
                    break
            klen = [len(k) for k in sort_kpath] 
            if len(klen) < kklen:
                kklen =len(klen)
            else:
                kid = np.argmax(klen)
                sorted_kpath.append(sort_kpath.pop(kid))
                klen.pop(kid)
                kklen = len(klen)
        sorted_kpath.append(sort_kpath[0]) 
        self.__kpath__ = sorted_kpath

    @classmethod
    def read_kpath(self,path):
        from jamip.utils.convert import kpath2list 

        file = os.path.join(path,'KPATH.in')
        if not os.path.exists(file):
            raise IOError('KPATH.in not exists!')
        with open(file,'r') as f:
            # skip title
            for i in range(3):
                f.readline()

            kpath = []
            kpaths = []
            insert = []
            # read kpath
            for line in f:
                if len(line.split()) == 6:
                    data = line.split()
                    if int(data[3]) == 0: continue
                    elif int(data[3]) == 1:
                        kpath.append(data[5])
                        kpaths.append(kpath)
                        kpath = []
                    else:
                        insert.append(int(data[3]))
                        kpath.append(data[5])

            if len(kpath) > 0:
                kpaths.append(kpath)

        insert = np.array(insert,dtype=int)
        index = np.concatenate(([0,], np.cumsum(insert)))
        kpath = kpath2list(kpaths)
        #return np.array((kpath, index)).T

        return kpath,index
        

class GrepBand(GrepOutcar):

    def _get_band(self,path):
        # if gw band %
        ialgo = self.ialgo(path)
        if ialgo == 4:
            return self._get_gw_band(path)
        ispin = self.ispin(path)
        nkpts = self.nkpts(path)
        nband = self.nbands(path)
        banddat = self.grep_band(path,nband)
        assert len(banddat) == ispin*nkpts*nband
        bands = []
        for dat in banddat:
            value = dat.split()
            if len(value)!= 3: continue
            bands.append(value[1:])
        bands = np.array(bands,dtype=float).reshape(ispin,nkpts,nband,2)
        return bands

    def _get_gw_band(self,path,last=True):
        gw_nelm = self.gw_nelm(path)
        assert gw_nelm > 0
        ispin = self.ispin(path)
        nkpts = self.nkpts(path)
        nband = self.nbands(path)+1
        banddat = self.grep_band(path,nband)
        assert len(banddat) == gw_nelm*ispin*nkpts*(nband)
        bands = []
        if last is True: 
            for i,dat in enumerate(banddat[-ispin*nkpts*nband:]):
                value = dat.split()
                if len(value)!= 7: 
                    continue
                bands.append([value[2],value[-1]])
            bands = np.array(bands,dtype=float).reshape(ispin,nkpts,nband-1,2)
        return bands

    def _get_kpoint(self,path,weight=False):
        nkpts = self.nkpts(path)
        kpointdat=self.grep_kpoint(path,nkpts)
        kpoints = []
        if weight:
            for dat in kpointdat:
                kpoints.append(dat.split()[:4])
        else:
            for dat in kpointdat:
                kpoints.append(dat.split()[:3])
        return np.array(kpoints,dtype=float)
 
    def _get_emass(self,bands=None,kpoints=None,rec_vector=None,axis=None,bd=['cbm','vbm'],fit_range=3):
        from scipy.optimize import curve_fit
        import scipy.constants as sc
        if not isinstance(bands,np.ndarray):
            bands = self.get_bands()
        if not isinstance(kpoints,np.ndarray):
            kpoints = self.get_kpoints()
        if not isinstance(rec_vector,np.ndarray):
            rec_vector = self.get_info('reciprocal_lattice_vectors')
        cbvbs = self.get_cbvb(bands=bands,isdata=True)
        mod=lambda x,a,b,c:a*x**2 + b*x + c

        def sliceByrange(length,index,range):
            if index < range:
                return slice(2*range+1)
            elif index+range >= length:
                return slice(-(2*range+1),length)
            else:
                return slice(index-range,index+range+1)

        def getStepsize(kpoints,rec_vector):
            kdiff = np.diff(kpoints,axis=0)
            kstep = [0]
            for k in kdiff:
                kstep.append(np.linalg.norm(k*rec_vector*sc.pi*2)/sc.angstrom)
            return np.cumsum(kstep)

        for vb,cb in cbvbs:  # spin-up % 
            emass = {}
            if 'cbm' in bd:
                _slice = sliceByrange(len(cb),np.argmin(cb),fit_range)
                yslice = cb[_slice]*sc.e
                xslice = getStepsize(kpoints[_slice],rec_vector)
                a,b,c = curve_fit(mod,xslice,yslice)[0]
                key = 'cbm-%s' %axis if axis!= None else 'cbm'
                emass[key]=np.around(sc.hbar**2/(2*a)/sc.electron_mass,6)
            if 'vbm' in bd:
                _slice = sliceByrange(len(vb),np.argmax(vb),fit_range)
                xslice = getStepsize(kpoints[_slice],rec_vector)
                yslice = vb[_slice]*sc.e
                a,b,c = curve_fit(mod,xslice,yslice)[0]
                key = 'vbm-%s' %axis if axis!= None else 'vbm'
                emass[key]=np.around(sc.hbar**2/(-2*a)/sc.electron_mass,6)
            return emass

class GrepProcar(GrepBand):

    def _procar_info(self,path):
        if not os.path.exists(os.path.join(path,'PROCAR')): 
            raise IOError("File 'PROCAR' not exists!") 
        else:       
            with open(os.path.join(path,'PROCAR'),'r') as f:
                f.readline()
                line = f.readline()
        return line

    def nkpts(self,path):
        if os.path.exists(os.path.join(path,'PROCAR')):            
            return int(self._procar_info(path).split()[3])
        else:
            return super().nkpts(path)

    def nbands(self,path):
        if os.path.exists(os.path.join(path,'PROCAR')):            
            return int(self._procar_info(path).split()[7])
        else:
            return super().nbands(path)

    def nions(self,path):
        if os.path.exists(os.path.join(path,'PROCAR')):            
            return int(self._procar_info(path).split()[11])
        else:
            return sum([i[1] for i in self.atominfo(path)])

    def _get_kpoint(self,path,weight=False):
        nkpts = self.nkpts(path)
        kpointdat=self.grep_kpoint_procar(path,nkpts)
        kpoints = []
        if weight:
            for dat in kpointdat:
                kpoints.append(dat.split()[3:6].append(dat.split()[8]))
        else:
            for dat in kpointdat:
                kpoints.append(dat.split()[3:6])
        return np.array(kpoints,dtype=float)

    def _get_band(self,path):
        nband = self.nbands(path)
        nkpts = self.nkpts(path)
        ispin = self.ispin(path)
        banddat = self.grep_band_procar(path)
        assert len(banddat) == ispin*nkpts*nband        
        bands = []
        band = []
        num = 1
        for line in banddat:
            value = line.split()
            index = int(value[1])
            energy = float(value[4])
            occ = float(value[7])
            band.append([energy,occ])
            if index == nband:
                bands.append(band)
                band = []
                num +=1
                if num > nkpts*ispin:
                    break
        bands = np.array(bands,dtype=float)
        if ispin == 1:
            assert bands.shape == (nkpts,nband,2)
            bands = bands.reshape(1,nkpts,nband,2)
        elif ispin == 2:
            assert bands.shape == (nkpts*2,nband,2)
            bands = bands.reshape(2,nkpts,nband,2)
        else:
            raise KeyError("Invalid ispin value")
        return bands

    def _get_procar(self,path):
        nband = self.nbands(path)
        nkpts = self.nkpts(path)
        ispin = self.ispin(path)
        nions = self.nions(path)
        procardat = self.grep_procar(path,nions)
        procar = []
        for line in procardat:
            value = line.split()[1:]
            procar.append(value)
        if ispin == 1:
            assert len(procar) == nkpts*nband*(nions+1)
            procar = np.array(procar,dtype=float).reshape(1,nkpts,nband,nions+1,-1)
        elif ispin == 2:
            assert len(procar) == 2*nkpts*nband*(nions+1)
            procar = np.array(procar,dtype=float).reshape(2,nkpts,nband,nions+1,-1)
        return procar
        
