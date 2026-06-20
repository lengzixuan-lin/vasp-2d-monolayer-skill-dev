from .outcar import GrepOutcar
import numpy as np
import re
import os

class GrepDynamics(GrepOutcar):
 
    def __init__(self):
        pass

    def oszicar(self,path):
        results = []
        with open(os.path.join(path,'OSZICAR'),'r') as f:
            for line in f:
                if 'T=' in line:
                    results.append(re.findall('(\d+)\s*T=\s*(\d+\.\d*)\s*E=\s*(-?\d?\.\d+E[-+]?\d+)\s*F=\s*(-?\d?\.\d+E[-+]?\d+)\s*E0=\s*(-?\d?\.\d+E[-+]?\d+)*', line)[0])
        return np.array(results, dtype=float)
 
    def pressure(self,path):
        results = []
        with open(os.path.join(path,'OUTCAR'),'r') as f:
            for line in f:
                if 'total pressure' in line:
                    results.append(re.findall('total pressure\s*=\s*(-?\d+\.\d*)', line)[0])
        return np.array(results, dtype=float)

    def forces(self,path):
        results = []
        with open(os.path.join(path,'OUTCAR'),'r') as f:
            for line in f:
                if 'TOTAL-FORCE (eV/Angst)' in line:                    
                    force = []
                    f.readline()
                    for line in f:
                        if len(line.split()) != 6: break
                        force.append(line.split()[3:])
                    results.append(force)
        return np.array(results, dtype=float)

    def xdatcar(self, path):
        results = []
        with open(os.path.join(path,'XDATCAR'),'r') as f:
            comment = f.readline()
            scale = float(f.readline().strip()) 
            lattice = []
            for i in range(3):
                lattice.append(f.readline().split())
            lattice = np.array(lattice, dtype=float) * scale
            element = np.array(f.readline().split())
            number = np.array(f.readline().split(), dtype=int)
            position = []
            for line in f:
                if line.startswith('Direct configuration='):
                    if len(position) == np.sum(number):
                        results.append(position)
                    position = []
                else:
                    position.append(line.split())
            # final         
            if len(position) == np.sum(number):
                results.append(position)
            results = np.array(results, dtype=float)
            return lattice, results

    def velocities(self, path, filename='v.dat'):

        with open(os.path.join(path, filename), 'r') as f:
            results = []
            for line in f:
                results.append(line.split())
       
        with open(os.path.join(path,'XDATCAR'),'r') as f:
            for i in range(6):
                f.readline()
            natoms = np.array(f.readline().split(), dtype=int).sum()

        results = np.array(results, dtype=float)[:len(results)//natoms*natoms]
        results = results.reshape(-1,natoms,3)

        return results

    def msd(self, data, nrepeat, **kwargs):
        """
        For 1d array: [nstep] -> msd [nstep]                 # single atom
        For 2d array: [nstep, natoms] -> msd [nstep]         # 1D materials
        For 3d array: [nstep, natoms, 3] -> msd [nstep, 3]   # 3D materials
        
        nrepeat: length for msd calculation.
        
        kwargs:
            natoms (default=natoms): if given number of atoms is less than natoms, it will random select given number of atoms.
        """
        from .fmsd import msd as fmsd

        def random(data, natoms):
            from copy import deepcopy
            data=np.array(data)
            if natoms < data.shape[1]:
                atoms=np.random.choice(range(data.shape[1]), natoms)
                print('selected atoms:', atoms)
                deleted_atoms=np.setdiff1d(range(data.shape[1]), atoms)
                tmp=deepcopy(data)
                tmp=np.delete(tmp, deleted_atoms, axis=1)
                data=tmp
            return data

        msd = None
        data=np.array(data)
        if len(data.shape) == 1:
            msd = fmsd(data, nrepeat, len(data))

        elif len(data.shape) == 2:
            # check
            natoms=data.shape[1]
            if 'natoms' in kwargs:
                natoms=kwargs['natoms']
            data=random(data, natoms)
            
            for j in range(0, data.shape[1]): # natoms
                data0=data[:,j]
                tmp = fmsd(data0, nrepeat, len(data0))
                if msd is None:
                    msd=tmp
                else:
                    msd += tmp
            
            msd /= data.shape[1]

        elif len(data.shape) == 3:
            # check
            natoms=data.shape[1]
            if 'natoms' in kwargs:
                natoms=kwargs['natoms']
            data=random(data, natoms)
            
            msd=np.array([None]*data.shape[2])
            for k in range(0, data.shape[2]):         # directions
                for j in range(0, data.shape[1]):     # natoms
                    data0=data[:, j, k]
                    tmp=fmsd(data0, nrepeat, len(data0))
                    if msd[k] is None:
                        msd[k]=tmp
                    else:
                        msd[k] += tmp
            
            msd=np.transpose(msd.tolist())
            msd /= data.shape[1]
        return msd

    def autocorrection(self, data):
        """
        For 1d array: [nstep] -> ac [nstep]
        For 2d array: [nstep, natoms] -> ac [nstep]
        For 3d array: [nstep, natoms, 3] -> ac [nstep, 3]
        """
        from scipy.signal import correlate

        ac=None
        data=np.array(data)
        if len(data.shape) == 1:
            data0=data
            result=correlate(data0, data0, mode='full')#, method='auto')
            ac=result[result.size//2:]
        elif len(data.shape) == 2:
            result=None
            for j in range(0, data.shape[1]): # natoms
                data0=data[:,j]
                tmp=correlate(data0, data0, mode='full')#, method='auto')
                tmp=tmp[tmp.size//2:]
                if result is None:
                    result=tmp
                else:
                    result += tmp
            result=np.array(result.tolist())
            result /= data.shape[1] # divde natoms
            ac=result
        elif len(data.shape) == 3:
            result=np.array([None]*data.shape[2])
            for k in range(0, data.shape[2]): # directions
                for j in range(0, data.shape[1]): # natoms
                    data0=data[:,j,k]
                    tmp=correlate(data0, data0, mode='full')#, method='auto')
                    tmp=tmp[tmp.size//2:]
                    if result[k] is None:
                        result[k]=tmp
                    else:
                        result[k] += tmp
            result=np.transpose(result.tolist())
            result /= data.shape[1] # divde natoms
            ac=result
        return ac


