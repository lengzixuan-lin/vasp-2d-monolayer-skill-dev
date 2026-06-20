from .outcar import GrepOutcar
import pandas as pd
import numpy as np
import os
import re

ev = 1.60217648740E-19
h = 6.626068E-34
c = 299792458
shift = 0
sigma = 0.06/2.3548
sqrt_2pi = np.sqrt(2.0*np.pi)
Vc = 0.025851997434


class GrepOptics(GrepOutcar):
 
    def __init__(self):
        pass

    def _alpha_w(self, imag, real):

        #f=open('alpha_w.dat','w')
        #f.write("#  E(hv)   alpha_x       alpha_y       alpha_z       alpha_av        n_av**2\n")
        deltaE = real[1,0] - real[0,0]
        real[:,0] -= shift
        real[np.where(real[:,0] < 1e-3)] = 0.0

        alpha = []
        for R_eps in real:
     
            hv = R_eps[0]
            if hv > 5: break
            # imag cutoff %
            val = ( (imag[:,0]-hv) / sigma )**2/2.0
            imag_val = imag[np.where(val<15.0),1:]
            val = val[np.where(val<15.0)]
            I_eps = np.sum(np.exp(-val) * imag_val, axis=0) * deltaE / sqrt_2pi / sigma
            I_eps = I_eps[0]
     
            # transform matrix %
            Cxx = np.complex(R_eps[1], I_eps[0])
            Cyy = np.complex(R_eps[2], I_eps[1])
            Czz = np.complex(R_eps[3], I_eps[2])
            Cxy = np.complex(R_eps[4], I_eps[3])
            Cyz = np.complex(R_eps[5], I_eps[4])
            Czx = np.complex(R_eps[6], I_eps[5])
     
            C_eps = np.mat([[Cxx,          Cxy, np.conj(Czx)],
                            [np.conj(Cxy), Cyy,          Cyz],
                            [Czx,          np.conj(Cyz), Czz]])
            eps_eig, eps_v = np.linalg.eig(C_eps)
     
            alpha_a1 = hv * 71618.96076 * np.sqrt(np.abs(eps_eig[0])-np.real(eps_eig[0]))
            alpha_a2 = hv * 71618.96076 * np.sqrt(np.abs(eps_eig[1])-np.real(eps_eig[1]))
            alpha_a3 = hv * 71618.96076 * np.sqrt(np.abs(eps_eig[2])-np.real(eps_eig[2]))
            alpha_av = (alpha_a1 + alpha_a2 + alpha_a3)/3
     
            n1 = np.sqrt(0.5*(np.abs(eps_eig[0])+np.real(eps_eig[0])))
            n2 = np.sqrt(0.5*(np.abs(eps_eig[1])+np.real(eps_eig[1])))
            n3 = np.sqrt(0.5*(np.abs(eps_eig[2])+np.real(eps_eig[2])))
            n_av = (n1+n2+n3)/3.0
     
            #f.write("%9.4f %13.6E %13.6E %13.6E %13.6E %9.4f\n" %(hv, alpha_a1, alpha_a2, alpha_a3, alpha_av, n_av**2))
            alpha.append([hv, alpha_av, n_av**2])
     
        return np.array(alpha)

    def _alpha_am(self, alpha):

        module_dir = os.path.dirname(os.path.abspath(__file__))
        am15 = pd.read_csv(os.path.join(module_dir, 'AM15.csv')).values
        alpha_am = []
        for dat in am15:
 
            hv = dat[0]
            nhv = dat[1]
      
            for i in range(len(alpha)):
                if alpha[i][0] <= hv and alpha[i+1][0] >= hv:
                   fact = (hv - alpha[i][0])/(alpha[i+1][0] - alpha[i][0])
                   tmp1 = alpha[i][1]*(1-fact) + fact*alpha[i+1][1]
                   tmp2 = alpha[i][2]*(1-fact) + fact*alpha[i+1][2]
                   alpha_am.append([hv, nhv, tmp1, tmp2])
                   break
      
        return np.array(alpha_am)

    def _slme(self, alpha, L, Eg, dEg):

        Isc = 0.0
        I0  = 0.0

        aE = 1.0-np.exp(-2.0 * L * alpha[:,2])
        isc = alpha[:,1] * aE
        irb = alpha[:,0]**2 / (np.exp(alpha[:,0]/Vc)-1) * aE
       
        for l in range(len(alpha)-1) :
       
            des = alpha[l+1,0] - alpha[l,0]
            Isc += (isc[l] + isc[l+1]) * des / 2.0
            I0 += (irb[l] + irb[l+1]) * des / 2.0
       
        I0 = I0 * 2.0*np.pi*c/(h*c/ev)**3 * np.exp(dEg/Vc)
       
        npts = np.arange(0,Eg,0.001)
        IV = npts * ( Isc - I0 * np.exp(npts/Vc))
        slme = np.max(IV) * ev / 10

        return slme
      
      
  
      
