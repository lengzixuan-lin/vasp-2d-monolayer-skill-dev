"""
Created on Mon Apr 15 20:57:39 2019

@author: lits
"""
from .outcar import GrepOutcar
import numpy as np
import os
import sys
import xrayutilities as xru
from jamip.structure import read

class GrepXarys(GrepOutcar):

    def __init__(self):
        pass

    def get_formula(self,path):
        struct = read(path)
        return struct.get_format()

    def get_crystal(self,path):
        from xrayutilities.materials.material import Crystal
        return Crystal.fromCIF(path)

    def create_xrd(self,path):
        crystal = self.get_crystal(path)
        pd = xru.simpack.PowderDiffraction(crystal)

        Am_max = max([float(pd.data[i]['r']) for i in pd.data])
        HKL = []
        for key,value in pd.data.items():
            if value['active'] is True:
                tmp = {}
                tmp['theta*2'] = value['ang']*2
                tmp['Amplitude'] = value['r'] / Am_max * 100
                tmp['d_spacing'] = pd.wavelength / (2 * np.sin(value['ang'] * np.pi / 180))
                tmp['hkl'] = key
                HKL.append(tmp)

        return HKL

    def plot_xrd(self,path,savepath=None):
        from xrayutilities.simpack.powdermodel import plot_powder
        plot, plt = xru.utilities.import_matplotlib_pyplot('XU.simpack')
        crystal = self.get_crystal(path)
        pd = xru.simpack.PowderDiffraction(crystal,enable_simulation=True)
        twotheta = np.arange(20,90,0.1)
        # sim = pd.Convolve(twotheta,mode='local')
        sim = pd.Calculate(twotheta,mode='local')
        plot_powder(twotheta,None,sim)
        if savepath is None:
            plt.show()
        else:
            plt.savefig(os.path.join(savepath,'xrd.png'))
        # xrd_dict = {"meta": ["amplitude", "hkl", "two_theta", "d_spacing"], \
        #                 "created_at": "2019-04", \
        #                 "wavelength": {"element": "Cu", "in_angstroms": 1.54184}, 
        #                 "pattern": []}
