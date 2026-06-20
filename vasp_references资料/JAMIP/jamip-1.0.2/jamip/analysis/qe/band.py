from .qexml import GrepXml
import numpy as np
import os

class GrepBand(GrepXml):

    def __init__(self):
        pass

    def _get_band(self,xmlfile):
        # ispin
        nk = self.nk(xmlfile)
        nbnd = self.nbnd(xmlfile)
        banddat = self.bands(xmlfile)
        assert banddat.shape == (nk,nbnd,2)
        # unit hartree > eV %
        banddat[:,:,0] *=  27.211629
        return banddat

    def _get_kpoint(self,xmlfile,weight=False):
        nk = self.nk(xmlfile)
        kpoints = self.kpoints(xmlfile)
        assert len(kpoints) == nk
        if weight:
            kpoints_weight = self.kpoints_weight(xmlfile)
            kpoints = np.stack((kpoints,kpoints_weight),axis=2)
        return kpoints

    def _get_kpath(self,infile):
        if not os.path.exists(infile):
            raise OSError("QE INPUTFILE not exists! seek kpath failed.")
        inserts = []
        kpaths = []
        kpath = []
        sum = 0
        with open(infile,'r') as f:
            for line in f:
                if 'K_POINTS' in line and line.split()[1] == 'crystal_b':
                    num = int(f.readline())
                    for i in range(num):
                        line = f.readline().split()
                        kpath.append(line[-1])
                        sum += int(line[3])
                        if int(line[3]) > 1:
                            inserts.append(sum)
                        else:
                            kpaths.append(kpath)
                            kpath = []
            if len(kpath):
                kpaths.append(kpath)
                     
        return kpaths,inserts
                        


if __name__ == "__main__":
    xmlfile = "/home/kzhou/qest/TEST/Si.vasp/qerun/band.xml"
    banddat = GrepBand()._get_band(xmlfile)
    kpoints = GrepBand()._get_kpoint(xmlfile)
    print(kpoints)
