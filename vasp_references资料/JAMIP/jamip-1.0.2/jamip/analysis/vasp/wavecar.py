from jamip.structure import read
from .outcar import GrepOutcar
import numpy as np
import spglib
import os

# constant %
lsoc = False  # if calculation with vasp_ncl
lgam = False  # if calculation with vasp_gam
gam_half = 'x'
RYTOEV   = 13.605826
TPI    = 2 * np.pi
AUTOA    = 0.529177249
HSQDTM = RYTOEV * AUTOA * AUTOA
AUTDEBYE = 2.541746
# HSQDTM    =  hbar**2/(2*ELECTRON MASS)

def setWFPrec(rtag):
    '''
    Set wavefunction coefficients precision:
    TAG = 45200: single precision complex, np.complex64, or complex(qs)
    TAG = 45210: double precision complex, np.complex128, or complex(q)
    '''
    if rtag == 45200:
        return np.complex64
    elif rtag == 45210:
        return np.complex128
    elif rtag == 53300:
        raise ValueError("VASP5 WAVECAR format, not implemented yet")
    elif rtag == 53310:
        raise ValueError("VASP5 WAVECAR format with double precision "
                            +"coefficients, not implemented yet")

class GrepWavecar(object):


    def __init__(self,stdin='.'):
        self.stdin = stdin

    def wavecar_info(self,input):
        input.seek(0) 
        dump = np.fromfile(input, dtype=np.float, count=3)
        self.recl = int(dump[0])
        self.nspin = int(dump[1])
        self.prec = setWFPrec(int(dump[2]))
        input.seek(dump[0])
        dump = np.fromfile(input, dtype=np.float64, count=12)
        self.nkpts  = int(dump[0])              # No. of k-points
        self.nbands = int(dump[1])              # No. of bands
        self.encut  = dump[2]                   # Energy cutoff
        cell = dump[3:].reshape((3,3))    # real space supercell basis
        self.rec_cell  = 2*np.pi*np.linalg.inv(cell).T
       
        # Minimum FFT grid size
        Anorm = np.linalg.norm(cell, axis=1)
        CUTOF = np.ceil(np.sqrt(self.encut/RYTOEV)/(TPI/(Anorm/AUTOA)))
        self.ngrid = np.array(2 * CUTOF + 1, dtype=int)
     
        return input

    def seekRec(self,ispin,ikpt,iband,shift=0):
        assert 0 <= ispin < self.nspin
        assert 0 <= ikpt < self.nkpts
        assert 1 <= iband <= self.nbands
        rec = 2 + ispin * self.nkpts * (self.nbands+1) + \
              ikpt * (self.nbands+1) + iband + shift
        self.input.seek(rec * self.recl)

    def wavecar(self,filename="WAVECAR", **kwargs):

        self.input = open(os.path.join(self.stdin,filename),'r')
        self.wavecar_info(self.input)
        self.nplws = np.zeros(self.nkpts, dtype=int)
        self.kvecs = np.zeros((self.nkpts, 3), dtype=np.float64)
        self.bands = np.zeros((self.nspin, self.nkpts, self.nbands), dtype=float)
        self.occs  = np.zeros((self.nspin, self.nkpts, self.nbands), dtype=float)
 
        if 'lsorbit' in kwargs:
            self.lsorbit = kwargs['lsorbit']
        else:
            self.lsorbit = GrepOutcar().lsorbit(self.stdin)

        for ii in range(self.nspin):
            for jj in range(self.nkpts):
                self.seekRec(ii, jj, 1, -1)
                dump = np.fromfile(self.input, dtype=np.float, 
                                   count=4+3*self.nbands)
                if ii == 0:
                    self.nplws[jj] = int(dump[0])
                    self.kvecs[jj] = dump[1:4]
                dump = dump[4:].reshape((-1, 3))
                self.bands[ii,jj,:] = dump[:,0]
                self.occs[ii,jj,:] = dump[:,2]

    def read_unfolding(self):
        from os.path import join,exists

        KPOINTS = join(self.stdin,'KPOINTS') 
        GPOINTS = join(self.stdin,'GPOINTS') 
        if not exists(KPOINTS) or not exists(GPOINTS):
            raise IOError("File not exists!")

        with open(KPOINTS,'r') as f:
            for line in f:
                if line.lstrip()[0].lower() == 'r':
                    break
            KPTS = []
            for line in f:
                if len(line.split()) == 4:
                    KPTS.append(line.split())
            KPTS = np.array(KPTS,dtype=np.float)[:,:3]

        with open(GPOINTS,'r') as f:
            for line in f:
                if line.lstrip()[0].lower() == 'r':
                    break
            GPTS = []
            for line in f:
                if len(line.split()) == 4:
                    GPTS.append(line.split())
            GPTS = np.array(GPTS,dtype=np.float)[:,:3].astype(int)

        KPTS = KPTS + GPTS

        return KPTS,GPTS

    def readBandCoeff(self, ispin, ikpt, iband, norm=False):
        '''
        Read the planewave coefficients of specified KS states.
        '''
        #print(ispin,ikpt,iband)
        self.seekRec(ispin, ikpt, iband+1)
        dump = np.fromfile(self.input, dtype=self.prec, 
                           count=self.nplws[ikpt])
        cg = np.asarray(dump, dtype=np.complex128)
        if norm:
            cg /= np.linalg.norm(cg)
        return cg

    def spectral_weight(self,G):
        assert len(G) == self.nkpts
        SW = []
        for ispin in range(self.nspin):
            SW.append(self._spectral_weight(G,ispin))

        return np.array(SW)

    def spectral_function(self, SW, nedos=4000, sigma=0.02):
        SF = np.zeros((self.nspin,nedos,self.nkpts))
        bands = self.bands
        emin = bands.min()
        emax = bands.max()
        e0 = np.linspace(emin -5 * sigma , emax + 5*sigma, nedos)
        LorentzSmearing=lambda x,x0,sigma: 1./ np.pi * sigma**2 / ((x - x0)**2 + sigma**2)

        for ispin in range(self.nspin):
            for ii in range(self.nkpts):
                E_Km = bands[ispin,ii,:]
                P_Km = SW[ispin,ii,:]
                SF[ispin,:,ii] = np.sum(LorentzSmearing(e0[:,np.newaxis], E_Km[np.newaxis,:],
                              sigma=sigma)* P_Km[np.newaxis,:], axis=1)
        return e0, SF
        

    def _spectral_weight(self,G,ispin):
        # assert input KPTS valid %
        assert len(G) == self.nkpts
        nbands = self.nbands

        SW = []
        for ikpt,g in enumerate(G):
            Gvalid, Gall = self.get_ovlap_G(ikpt)
            Goffset = Gvalid + g[np.newaxis, :]
  
            # Index of the Gvalid in 3D grid
            GallIndex = Gall % self.ngrid[np.newaxis, :]
            GoffsetIndex = Goffset % self.ngrid[np.newaxis, :]
  
            # 3d grid for planewave coefficients
            wfc_k_3D = np.zeros(self.ngrid, dtype=np.complex)
  
            if self.lsorbit:
                # the weights and corresponding energies
                P_Km = np.zeros((2,nbands), dtype=float)
                E_Km = np.zeros((2,nbands), dtype=float)
            else:
                # the weights and corresponding energies
                P_Km = np.zeros(nbands, dtype=float)
                E_Km = np.zeros(nbands, dtype=float)

            for nb in range(nbands):
                # initialize the array to zero, which is unnecessary 
                # since the GallIndex is the same for the same K-point
                # wfc_k_3D[:,:,:] = 0.0
  
                if lsoc:
                    # pad the coefficients to 3D grid
                    band_coeff = self.readBandCoeff(ispin, ikpt, nb, norm=False)
                    nplw = band_coeff.shape[0] / 2
                    band_spinor_coeff = [band_coeff[:nplw], band_coeff[nplw:]]
  
                    for Ispinor in range(2):
                        band = band_spinor_coeff[Ispinor]
                        band /= np.linalg.norm(band)
                        wfc_k_3D[GallIndex[:,0], GallIndex[:,1], GallIndex[:,2]] = band
  
                        # energy
                        E_Km[Ispinor, nb] = self.bands[ispin-1,ikpt,nb]
                        # spectral weight
                        P_Km[Ispinor, nb] = np.linalg.norm(
                                    wfc_k_3D[GoffsetIndex[:,0], GoffsetIndex[:,1], GoffsetIndex[:,2]]
                                )**2
                else:
                    # pad the coefficients to 3D grid
                    band_coeff = self.readBandCoeff(ispin, ikpt, nb, norm=True)
                    if lgam:
                        nplw = band_coeff.size
                        tmp  = np.zeros((nplw * 2 - 1), dtype=band_coeff.dtype)
                        # for Gamma version, the coefficients corresponding to G \ne 0
                        # is multiplied by a factor of sqrt(2)
                        band_coeff[1:] /= np.sqrt(2.)
                        tmp[:nplw] = band_coeff
                        tmp[nplw:] = band_coeff[1:].conj()
                        band_coeff = tmp
  
                    wfc_k_3D[GallIndex[:,0], GallIndex[:,1], GallIndex[:,2]] = band_coeff
                    # energy
                    E_Km[nb] = self.bands[ispin-1,ikpt,nb]
                    # spectral weight
                    P_Km[nb] = np.linalg.norm(
                                wfc_k_3D[GoffsetIndex[:,0], GoffsetIndex[:,1], GoffsetIndex[:,2]]
                            )**2
                #return np.array((E_Km, P_Km), dtype=float).T
            SW.append(P_Km)
        return np.array(SW,dtype=float)

    def get_ovlap_G(self,ikpt,epsilon=1e-5):

        # Reciprocal space vectors of the supercell in fractional unit
        Gvecs = self.gvectors(ikpt)
 
        if lgam:
            nplw = Gvecs.shape[0]
            tmp  = np.zeros((nplw * 2 - 1, 3), dtype=int)
            tmp[:nplw,...] = Gvecs
            tmp[nplw:,...] = -Gvecs[1:,...]            # G' = -G
            Gvecs = tmp
 
        # Shape of Gvecs: (nplws, 3)
        # iGvecs = np.arange(Gvecs.shape[0], dtype=int)
 
        # Reciprocal space vectors of the primitive cell
        gvecs = np.dot(Gvecs, np.linalg.inv(self.trans).T)
        # Deviation from the perfect sites
        gd = gvecs - np.round(gvecs)
        # match = np.linalg.norm(gd, axis=1) < epsilon
        match = np.alltrue(np.abs(gd) < epsilon, axis=1)
 
        return Gvecs[match], Gvecs
        
    def gvectors(self, ikpt, check_consistency=True):
        '''                           
        Generate the G-vectors that satisfies the following relation
            (G + k)**2 / 2 < ENCUT        
        '''                               
        kvec = self.kvecs[ikpt]
        if kvec[2] - 0.5 > -1e-8:
            kvec[2] -= 1

        ngrid = self.ngrid
        nplws = self.nplws
        fx, fy, fz = [np.arange(n, dtype=int) for n in ngrid]
        fx[ngrid[0] // 2 + 1:] -= ngrid[0]
        fy[ngrid[1] // 2 + 1:] -= ngrid[1]
        fz[ngrid[2] // 2 + 1:] -= ngrid[2]

        '''
        fx = [ii if ii < ngrid[0] / 2 + 1 else ii - ngrid[0]
                for ii in range(ngrid[0])]
        fy = [jj if jj < ngrid[1] / 2 + 1 else jj - ngrid[1]
                for jj in range(ngrid[1])]
        fz = [kk if kk < ngrid[2] / 2 + 1 else kk - ngrid[2]
                for kk in range(ngrid[2])]
        '''
        if lgam:
            if gam_half == 'x':
                fx = fx[:ngrid[0] // 2 + 1]
            else:
                fz = fz[:ngrid[2] // 2 + 1]

        '''
        if lgam:                  
            # parallel gamma version of VASP WAVECAR exclude some planewave components, -DwNGZHalf
            if gam_half == 'z':
                kgrid = np.array([(fx[ii], fy[jj], fz[kk])
                                  for kk in range(ngrid[2])
                                  for jj in range(ngrid[1])
                                  for ii in range(ngrid[0])
                                  if (
                                      (fz[kk] > 0) or
                                      (fz[kk] == 0 and fy[jj] > 0) or
                                      (fz[kk] == 0 and fy[jj] == 0 and fx[ii] >= 0)
                                  )], dtype=float)
            else:
                kgrid = np.array([(fx[ii], fy[jj], fz[kk])
                                  for kk in range(ngrid[2])
                                  for jj in range(ngrid[1])
                                  for ii in range(ngrid[0])
                                  if (
                                      (fx[ii] > 0) or
                                      (fx[ii] == 0 and fy[jj] > 0) or
                                      (fx[ii] == 0 and fy[jj] == 0 and fz[kk] >= 0)
                                  )], dtype=float)
        else:
            kgrid = np.array([(fx[ii], fy[jj], fz[kk])
                              for kk in range(ngrid[2])
                              for jj in range(ngrid[1])
                              for ii in range(ngrid[0])], dtype=float)
        '''
        gz, gy, gx = np.array(np.meshgrid(fz, fy, fx, indexing='ij')).reshape(3,-1)  
        kgrid = np.array([gx,gy,gz], dtype=float).T
        if lgam:
            if gam_half == 'z':
                kgrid = kgrid[(gz>0) | ((gz==0)&(gy>0)) | ((gz==0)&(gy==0)&(gx>=0))]
            else:
                kgrid = kgrid[(gx>0) | ((gx==0)&(gy>0)) | ((gx==0)&(gy==0)&(gz>=0))]

        KENERGY = HSQDTM * np.linalg.norm(np.dot(kgrid + kvec[np.newaxis,:], self.rec_cell), axis=1)**2
        # find Gvectors where (G + k)**2 / 2 < ENCUT
        Gvec = kgrid[np.where(KENERGY < self.encut)[0]]
 
        # Check if the calculated number of planewaves and the one recorded in the
        # WAVECAR are equal
        if check_consistency:
            '''
            if lsoc:
                assert Gvec.shape[0] == nplws[ikpt] / 2, 'No. of planewaves not consistent for an SOC WAVECAR! %d %d %d' % \
                    (Gvec.shape[0], nplws[ikpt], np.prod(ngrid))
            else:
                assert Gvec.shape[0] == nplws[ikpt], 'No. of planewaves not consistent! %d %d %d' % \
                    (Gvec.shape[0], nplws[ikpt], np.prod(ngrid))
            '''
            if Gvec.shape[0] != self.nplws[ikpt]:
                if Gvec.shape[0] * 2 == self.nplws[ikpt]:
                    if not self.lsorbit:
                        raise ValueError('try lsobtib=True')

                elif Gvec.shape[0] == 2 * self.nplws[ikpt]:
                    if not lgam:
                        raise ValueError('try lgamma=True')

                else:
                    raise ValueError('''
                    NO. OF PLANEWAVES NOT CONSISTENT:
                        THIS CODE -> %d
                        FROM VASP -> %d
                           NGRIDS -> %d
                    ''' % (Gvec.shape[0],
                           self.nplws[ikpt] // 2 if self.lsorbit else self.nplws[ikpt],
                           np.prod(ngrid))
                    )

        return np.asarray(Gvec, dtype=int)

    def _get_dipole_ovlap(self):
        edges = self.get_edge_band()
        ovlaps = []
        tdms = []
        dEs = []
        for ispin in range(self.bands.shape[0]):
            for ikpt in range(self.bands.shape[1]):
                cbk = [ispin,ikpt,edges[ispin]]
                vbk = [ispin,ikpt,edges[ispin]-1]
                tmp = self.dipole(vbk,cbk)
                dEs.append(tmp[0])
                ovlaps.append(tmp[1].real)
                tdms.append(np.abs(tmp[2])**2)
        self.ovlaps = np.array(ovlaps)
        self.tdms = np.array(tdms)

    def get_dipole(self):
        self._get_dipole_ovlap()
        return self.tdms

    def get_ovlap(self):
        self._get_dipole_ovlap()
        return self.ovlaps
  
    def dipole(self,ki,kj): 
        '''
        K = [ispin,ikpt,iband]
        '''
        Eki = self.bands[ki[0],ki[1],ki[2]]
        Ekj = self.bands[kj[0],kj[1],kj[2]]
        dE = Ekj - Eki
        gvec = np.dot(self.gvectors(ikpt=ki[1]), self.rec_cell)

        phi_i = self.readBandCoeff(*ki, norm=True)
        phi_j = self.readBandCoeff(*kj, norm=True)
        tmp1 = phi_i.conjugate() * phi_j
        ovlap = np.sum(tmp1)
        if lgam:
            tmp2 = phi_i * phi_j.conjugate()
            tdm = (np.sum(tmp1[:, np.newaxis] * gvec, axis=0) -
                   np.sum(tmp2[:, np.newaxis] * gvec, axis=0)) / 2.
        elif self.lsorbit:
            tdm = np.sum(tmp1[:, newaxis] * np._r[gvec, gvec], axis=0)
        else:
            tdm = np.sum(tmp1[:, np.newaxis] * gvec, axis=0)

        tdm = 1j / (dE / (2*RYTOEV)) * tdm * AUTOA * AUTDEBYE

        return dE, ovlap, tdm

    def get_edge_band(self):
        nbs = []
        for ispin in range(self.occs.shape[0]):
            for iband in range(self.occs.shape[2]):
                if max(self.occs[ispin,:,iband]) < 0.001:
                    nbs.append(iband)
                    break
        return nbs


    def wave_overlap(self):
        '''
        K = [ispin,ikpt,iband]
        '''
        # assert input KPTS valid %
        edges = self.get_edge_band()
        for ispin in range(self.bands.shape[0]):
            # get edge kpt cbm %
            kpt_c = np.argmin(self.bands[ispin,:,edges[ispin]])
            kpt_v = np.argmax(self.bands[ispin,:,edges[ispin]-1])

            # get WAV %
            WAVC = self.readBandCoeff(ispin,kpt_c,edges[ispin],norm=True)
            WAVV = self.readBandCoeff(ispin,kpt_v,edges[ispin]-1,norm=True)

            # fill data into ngrid %
            # cbm %
            WAVCALL = np.zeros(self.ngrid, dtype=np.complex)
            CIndex = self.gvectors(kpt_c) % self.ngrid[np.newaxis, :]
            WAVCALL[CIndex[:,0], CIndex[:,1], CIndex[:,2]] = WAVC
            # vbm %
            WAVVALL = np.zeros(self.ngrid, dtype=np.complex)
            VIndex = self.gvectors(kpt_v) % self.ngrid[np.newaxis, :]
            WAVVALL[VIndex[:,0], VIndex[:,1], VIndex[:,2]] = WAVV

        ovlap_3D = np.abs(WAVCALL) * np.abs(WAVVALL)
        self.ovlap = ovlap_3D

        return np.sum(ovlap_3D)**2


# wavecar %
if __name__ == "__main__":
    w = GrepWavecar()
    w.wavecar()
    pdms = w.get_dipole()
    tdms = np.sum(pdms,axis=1)
    w.plot_tdm(tdms)

