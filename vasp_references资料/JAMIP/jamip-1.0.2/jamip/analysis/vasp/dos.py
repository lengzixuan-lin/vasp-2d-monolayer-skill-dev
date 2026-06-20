from .outcar import GrepOutcar
import numpy as np
import os

class GrepDos(GrepOutcar):
 
    def __init__(self):
        pass

    def _doscar_info(self,path):
        with open(os.path.join(path,'DOSCAR'),'r') as f:
            for i in range(5):
                f.readline()
            line = f.readline()
        return line
 
    def fermi_energy(self,path):
        return float(self._doscar_info(path).split()[3])

    def emin(self,path):
        return float(self._doscar_info(path).split()[1])

    def emax(self,path):
        return float(self._doscar_info(path).split()[0])

    def nedos(self,path):
        return int(self._doscar_info(path).split()[2])

    def _get_tdos(self,path):
        nedos = self.nedos(path)
        doses = []        
        with open(os.path.join(path,"DOSCAR"),'r') as f:
            for i in range(6): 
                f.readline()
            dos=[]
            for i in range(nedos):
                dos.append(f.readline().split())
            dos = np.array(dos,dtype=float)
        return dos

    def _get_pdos(self,path):
        nedos = self.nedos(path)
        doses = []        
        with open(os.path.join(path,"DOSCAR"),'r') as f:
            for i in range(nedos+6): 
                f.readline()
            while f.readline():
                dos=[]
                for i in range(nedos):
                    dos.append(f.readline().split())
                doses.append(dos)
            doses = np.array(doses,dtype=float)
        return doses
