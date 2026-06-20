import os
import numpy as np

class GrepDos:
   
    def __init__(self):
        pass

    def fermi_energy(self,path):
        #path = os.path.join(path,'dos.plt.dat')
        with open(path,'r') as f:
            data = float(f.readline().split()[-2])
        return data

    def _get_tdos(self,path):
        #path = os.path.join(path,'dos.plt.dat')
        with open(path,'r') as f:
            f.readline()
            tdos = []
            for line in f:
                if '*' in line: continue
                tdos.append(line.split())
        tdos = np.array(tdos,dtype=float)
        return tdos

    def _get_pdos(self,path):
        pass



