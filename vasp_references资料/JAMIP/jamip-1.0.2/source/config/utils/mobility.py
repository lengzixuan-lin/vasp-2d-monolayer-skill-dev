import os
from os.path import join
import numpy as np
import pandas as pd
from jamip.analysis.vasp import BandFinder
from jamip.analysis.vasp.outcar import GrepOutcar
from jamip.structure import read
from scipy.optimize import curve_fit
import scipy.constants as sc
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt


def get_emass(path, vaccum_level=0, axis=None):
    Ecbm = []
    Evbm = []
    result = {}

    for dir in os.listdir(path):
        keys = dir.split('-')
        if axis != None and keys[0] not in axis:
            continue
        if len(keys) > 1:
            edge = bf.get_cbmvbm(join(path,dir))
            Ecbm.append(edge['cbm']['energy'])
            Evbm.append(edge['vbm']['energy'])
            tmp = bf.get_emass(join(path,dir))
            for i in keys[1:]:
                result['%s-%s' %(i,keys[0])] = tmp[i]

    result['Ecbm'] = np.round(np.mean(Ecbm)-vaccum_level,4)
    result['Evbm'] = np.round(np.mean(Evbm)-vaccum_level,4)
    return result

axis = ['x','y']
coef = [0.98,0.99,1.00,1.01,1.02]
line = lambda x,a,b:a*x + b
mod = lambda x,a,b,c:a*x**2 + b*x + c
rootdir = 'Output/GaN.vasp'

# mobility-1.00 %
bf = BandFinder(rootdir)
vaccum_level=bf.get_locpot(axis='z')
structure = read(rootdir+'/scf/CONTCAR')
a,b,c,alpha,beta,gamma = structure.lattice_parameters
sectional_area = a*b*np.sin(gamma)
mobi0 = pd.Series(get_emass(rootdir+'/electric/emass', vaccum_level, axis))
mobi0['Efree'] = GrepOutcar().free_energy(rootdir+'/scf')
md_c = np.sqrt(mobi0['cbm-x'] * mobi0['cbm-y'])
md_v = np.sqrt(mobi0['vbm-x'] * mobi0['vbm-y'])

if os.path.exists('mobi.csv'):
    mobis = pd.read_csv('mobi.csv', index_col=0)
    print(mobis)
else:
    mobis = pd.DataFrame()
    for j in axis:
        for scale in coef:
            key = '{}-{}'.format(j, scale)
            if abs(scale-1) < 1e-4:
                mobi0 = mobi0.rename(key)
                mobis = mobis.append(mobi0)
                continue
            path = join(rootdir, 'electric', 'mobility', key)
            vaccum_level = bf.get_locpot(path+'/scf',axis='z')
            data = pd.Series(get_emass(path, vaccum_level, axis), name=key)
            data['Efree'] = GrepOutcar().free_energy(path+'/scf')
            mobis = mobis.append(data)
    mobis.to_csv('mobi.csv')

for j in axis:
    index = [i for i in mobis.index if j in i]
    Efree = mobis.loc[index,'Efree'].values.transpose()
    Ecbm  = mobis.loc[index,'Ecbm' ].values.transpose()
    Evbm  = mobis.loc[index,'Evbm' ].values.transpose()

    stretch,b,c = curve_fit(mod,coef,Efree)[0]
    deform_c,b = curve_fit(line,coef,Ecbm)[0]
    deform_v,b = curve_fit(line,coef,Evbm)[0]
   
    stretch = stretch*2*sc.e/(sectional_area*sc.angstrom**2)
    deform_c = deform_c*sc.e
    deform_v = deform_v*sc.e
    m_c = mobi0['cbm-%s' %j]
    m_v = mobi0['vbm-%s' %j]
    T = 300
    mu_c = sc.e*sc.hbar**3*stretch/(sc.k*T*m_c*md_c*sc.electron_mass**2*deform_c**2)
    mu_v = sc.e*sc.hbar**3*stretch/(sc.k*T*m_v*md_v*sc.electron_mass**2*deform_v**2)
    print('-'*20)
    print('# Axis %s' %j)
    print('m_cbm = {0:.4f}'.format(m_c))
    print('m_vbm = {0:.4f}'.format(m_v))
    print('mu_cbm = {0:.4f} cm^2/(V*s)'.format(mu_c*1e4))
    print('mu_vbm = {0:.4f} cm^2/(V*s)'.format(mu_v*1e4))

    plt.figure(figsize=(6,6),dpi=144)
    size = 15
    plt.text(0.05,0.9 ,'$C_{2D_x}$'+' = {0:.4f}'.format(stretch),fontsize = size)
    plt.text(0.05,0.75,'$m^*_{x_{cbm}}$'+' = {0:.4f}$m_0$'.format(m_c),fontsize = size)
    plt.text(0.05,0.6 ,'$m^*_{x_{vbm}}$'+' = {0:.4f}$m_0$'.format(m_v),fontsize = size)
    plt.text(0.05,0.45,'$E_{I_{cbm}^x}$'+' = {0:.4f}eV'.format(-deform_c/sc.e),fontsize = size)
    plt.text(0.05,0.3 ,'$E_{I_{vbm}^x}$'+' = {0:.4f}eV'.format(-deform_v/sc.e),fontsize = size)
    plt.text(0.05,0.15,'$\mu_{2D_{cbm}^x}$'+' = {0:.4f} $cm^2/(V*s)$'.format(mu_c*1e4),fontsize = size)
    plt.text(0.05,0.0 ,'$\mu_{2D_{vbm}^x}$'+' = {0:.4f} $cm^2/(V*s)$'.format(mu_v*1e4),fontsize = size)
    ax = plt.gca()
    ax.set_axis_off()
    #ax.spines['top'].set_visible(False)
    #ax.spines['right'].set_visible(False)
    #ax.spines['bottom'].set_visible(False)
    #ax.spines['left'].set_visible(False)
    plt.savefig('m-%s.png' %j)

