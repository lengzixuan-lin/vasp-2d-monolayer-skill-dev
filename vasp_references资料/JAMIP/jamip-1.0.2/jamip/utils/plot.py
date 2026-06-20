import matplotlib 
matplotlib.use('agg')
import matplotlib.pyplot as plt
from jamip.analysis import Finder
from jamip.analysis.vasp import *
import numpy as np
import threading
import os

BAND_EMIN = -1
BAND_EMAX = 3
BAND_SHIFT = 0
BAND_XLABEL = ''
BAND_YLABEL = 'Energy (eV)'

DOS_EMIN = -1
DOS_EMAX = 3
DOS_LIMIT = 0.04
DOS_SHIFT = 0
DOS_XLABEL = 'Energy (eV)'
DOS_YLABEL = '$PDOS\ (states/eV/\AA^{3})$'

ABSORB_EMIN = 0
ABSORB_EMAX = 5
ABSORB_XLABEL = 'Energy (eV)'
ABSORB_YLABEL = '$Absorb (10^6 \cpot m^{-1}$)'

TDM_YLABEL = '$TDM\ P2^2(Debye^2)$'
DIEL_YLABEL = '$Arb.Unit$'
MESH = [10,10,10]
__all__ = ['BAND_EMIN','BAND_EMAX','BAND_SHIFT','BAND_XLABEL','BAND_YLABEL','DOS_EMIN','DOS_EMAX','DOS_LIMIT','DOS_XLABEL','DOS_YLABEL',
           'ABSORB_EMIN','ABSORB_EMAX','ABSORB_XLABEL','ABSORB_YLABEL','TDM_YLABEL','DIEL_YLABEL','MESH']

try:
    from plot import *
except:
    raise OSError("The plotting program name can only be plot.py ! ")

CMAP = ['g','b','y','m','orange','c','cyan','yellow','violet','brown',\
          'lime','deepskyblue','gold','darkorchid','greenyellow','r']
JOBLIST = {'pdos': 3, 'tdos':3, 'tdm':8, 'cohp':7,
           'band': 8, 'fatband':7, 'hseband':7 ,'unfolding':7,
           'absorb':7, 'dielectric':7,'cutoff_conv':7, 'kpoints_conv':7,
           'phband':7, 'phdos':3, 'gruneisen':7, 'softmode':7}
storage = os.path.join(os.environ['HOME'],'.jamip','viewer')
STYLES = {'base': os.path.join(storage,'base.mplstyle'),
          'band': os.path.join(storage,'band.mplstyle'),
          'dos': os.path.join(storage,'dos.mplstyle')}

class Figure:

    group = None
    savedir = None 
    figsize = (15,15) 
    styles = STYLES
    _instance_lock = threading.Lock()

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(Figure, "_instance"):
            with Figure._instance_lock:
                if not hasattr(Figure, "_instance"):
                    Figure._instance = object.__new__(cls)  
                    if cls.figsize != None:
                        plt.style.use(cls.styles['base'])
                        Figure.fig = plt.figure(figsize=cls.figsize)
                    else:
                        Figure.fig = plt.figure()
        return Figure._instance


    def figure(self, job, **kwargs):
        from os.path import join,exists

        if self.group != None:
            plt.style.use(self.styles[job])
            plt.subplot(self.group[job])
            
        return self

    def set_color(self,number=0):
        def colors(i):
            while True:
                yield CMAP[i]
                i+=1
        return colors(number)

    def set_axis(self, x, y):
        if self.group == None:
            return x,y
        else:
            return y,x

    @classmethod        
    def set_group(cls, jobs, **kwargs):

        from matplotlib.gridspec import GridSpec
        from os.path import exists,join

        mplstyle = lambda job: join(storage,job+'.mplstyle')

        # set style %
        for job in jobs:
            if exists(mplstyle(job)):
                cls.styles[job] = mplstyle(job)
            elif 'band' in job:
                cls.styles[job] = mplstyle('band')
            elif 'dos' in job or 'cohp' in job:
                cls.styles[job] = mplstyle('dos')
            else:
                cls.styles[job] = mplstyle('base')

        if 'slices' in kwargs and 'grid' in kwargs:
            ncols, nrows = kwargs["grid"]
            slices = kwargs["slices"]
            assert len(slices) == len(jobs)

            cls.figsize = (ncols,nrows)
            cls.group = {}
            gs = GridSpec(ncols,nrows)
            for job,slice in zip(jobs,slices):
                cls.group[job] = gs[slice[0],slice[1]]
 
        elif len(jobs) > 1 and cls.group == None:

            grid = [JOBLIST[job] for job in jobs]
            gs = GridSpec(1, np.sum(grid))
            cls.group = {}
            sum = 0 
            for k,i in zip(jobs,grid):
                cls.group[k] = gs[sum:sum+i]
                sum += i
            cls.figsize = (12*np.sum(grid)/np.max(grid),12)
       
        else:
            cls.group = None
            cls.figsize = None
            plt.style.use(cls.styles['base'])
            plt.style.use(cls.styles[jobs[0]])

    @classmethod
    def save(cls, jobs=None, dir=None):

            
        if cls.savedir != None:
            path = os.path.join(cls.savedir,os.path.basename(dir)+'.png')
        elif isinstance(jobs, list):
            path = ''.join(jobs)+'.png'
        elif isinstance(jobs, str):
            path = jobs
        else:
            raise TypeError
       
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        
        #if not hasattr(Figure, "_instance"):
        del Figure._instance


class Plot(Finder):

    _path_ = None
    _soft_ = 'vasp'

    def __init__(self, path=None, soft=None):
        if path != None:
            self.path = path
        if soft != None:
            self._soft_ = soft

    def plots(self,*args,**kwargs):
        '''
        main plot function
        '''
        from .phonoplot import PhononPlot
        jobs = []
        for job in args:
            if job in JOBLIST.keys():
                jobs.append(job)

        # job number %
        if len(jobs) == 0:
            raise KeyError("Invalid input job name.") 
        else:
            Figure.set_group(jobs, **kwargs)

        # path number %
        if len(self.path) == 0:
            raise IOError('No valid path for %s-plot' %job)
        elif len(self.path) > 1:
            Figure.savedir = ''.join(jobs)+'plot'
            if not os.path.exists(Figure.savedir):
                os.makedirs(Figure.savedir)
            print(''.join(jobs)+'plot')
        else:
            Figure.savedir = None

        success = 0
        errors = []
        for dir in self.path:
            try:
                for job in jobs:
                    if job == 'fatband':
                        plt = self.plot_fat_band(dir) 
                    elif job == 'band':
                        self.plot_band(dir)
                    elif job == 'tdos':
                        self.plot_dos(dir,'tdos')
                    elif job == 'pdos':
                        self.plot_dos(dir,'pdos')
                    elif job == 'tdm':
                        self.plot_tdm(dir)
                    elif job == 'absorb':
                        self.plot_absorb(dir)
                    elif job == 'dielectric':
                        self.plot_dielfunc(dir)
                    elif job == 'unfolding':
                        self.plot_unfolding(dir)
                    elif job == 'cohp':
                        self.plot_cohp(dir)
                    elif job == 'hseband':
                        self.plot_hseband(dir)
                    elif job == 'cutoff_conv':
                        self.plot_converge(dir, 'cutoff')
                    elif job == 'kpoints_conv':
                        self.plot_converge(dir, 'kpoints')
                    elif job == 'phband':
                        PhononPlot().band(dir)
                    elif job == 'phdos':
                        PhononPlot().dos(dir)
                    elif job == 'gruneisen':
                        PhononPlot().gruneisen(dir)
                    elif job == 'softmode':
                        PhononPlot().softmode(dir)

                Figure.save(jobs, dir)
                success += 1
            except:
                errors.append(dir)
        print('Success plot : %d' %success)
        if len(errors):
            print('Error paths as follows:')
            for path in errors:
                print(path)
          

    def plot_fat_band(self,path):
        '''
        plot band-figure base on PROCAR
        '''
        from .convert import kpath2list
        pf = ProFinder(path)
        fig = Figure().figure('band')
        color = fig.set_color()

        # grep main datas %
        bands=pf.get_bands() 
        procar,info,label=pf.get_pmax_procar()
        kpath=kpath2list(pf.kpath) 
        kpoints = pf.get_kpoints()
        nkpt = pf.get_insert()
        rec_vector = pf.get_info('reciprocal_lattice_vectors')

        # set x axis % 
        delta = [np.linalg.norm(np.dot(rec_vector,dk)) for dk in kpoints[1:]-kpoints[:-1] ]
        delta.insert(0,0)
        xkpt = np.cumsum(delta)
        xticks=[]
        for i in np.arange(0,len(kpoints)+1,nkpt):
            if i > 0: i -= 1
            xticks.append(xkpt[i])
            plt.axvline(xkpt[i],c='black')
        ax = plt.gca()
        ax.set_xticks(xticks)
        ax.set_xticklabels(kpath)

        # create colormap and legend%
        colormap = []
        linemap = []
        for i in range(len(label)):
            c = next(color)
            colormap.append(c)
            if np.sum(info == i) > nkpt:
                pl,=plt.plot([0,1],[0,1],c=c,label=label[i])
                linemap.append(pl)
        colormap = np.array(colormap)
        plt.legend(loc=1, fontsize='large', framealpha=0.9)
        for line in linemap:
            line.remove()

        # add bandgap %
        cv = pf.get_cbmvbm(bands)
        if cv['gap'] > 0:
            shift = cv['vbm']['energy']
            # plot bandgap %
            xvbm = xkpt[cv['vbm']['index'][1]]
            xcbm = xkpt[cv['cbm']['index'][1]]
            Ecbm = cv['cbm']['energy']-cv['vbm']['energy']+BAND_SHIFT
            plt.scatter([xvbm],[0],color='r',s=40)
            plt.plot([max(0,xcbm-xkpt[-1]/100),min(xkpt[-1],xcbm+xkpt[-1]/100)],[Ecbm,Ecbm],color='r') 
            plt.plot([xcbm,xcbm],[0,Ecbm],c='r',lw=2)
            xtext=[xcbm+xkpt[-1]/100,xcbm-xkpt[-1]/6][xcbm>xkpt[-1]*2/3]
            plt.text(xtext,Ecbm/2,'{:.3f} eV'.format(Ecbm))
        else:
            shift = pf.get_fermi()
        
        # plot band.png %
        for i,bands_ispin in enumerate(bands):
            ybands = bands_ispin[...,0] - shift
            if BAND_SHIFT != 0:
                ybands[:,cv['vbm']['index'][0]:] += BAND_SHIFT
            plt.plot(xkpt,ybands,c='k')
            for nband in range(len(ybands[0])):
                plt.scatter(xkpt,ybands[:,nband],color=colormap[info[i,:,nband]])

        plt.axhline(color='r',linestyle='--')
        plt.xlim(0,xkpt[-1])
        plt.ylim(BAND_EMIN,BAND_EMAX)
        plt.ylabel(BAND_YLABEL)

    def plot_band(self,path):
        '''
        plot band-figure base on OUTCAR
        '''
        # Initializes the data retrieval module & pyplot & colormap %
        from jamip.analysis.vasp import BandFinder
        from .convert import kpath2list
        bf = BandFinder(path)
        fig = Figure().figure('band')
        color = fig.set_color()

        # grep main datas %
        bands=bf.get_bands() 
        kpath=kpath2list(bf.kpath) 
        nkpt = bf.get_insert()
        kpoints = bf.get_kpoints()
        rec_vector = bf.get_info('reciprocal_lattice_vectors')

        # set x axis % 
        delta = [np.linalg.norm(np.dot(rec_vector,dk)) for dk in kpoints[1:]-kpoints[:-1] ]
        delta.insert(0,0)
        xkpt = np.cumsum(delta)
        xticks=[]
        for i in np.arange(0,len(kpoints)+1,nkpt):
            if i > 0: i -= 1
            xticks.append(xkpt[i])
            plt.axvline(xkpt[i],c='black')
        ax = plt.gca()
        #plt.xticks([])
        ax.set_xticks(xticks)
        ax.set_xticklabels(kpath)

        # add bandgap %
        cv = bf.get_cbmvbm(bands)
        if cv['gap'] > 0:
            shift = cv['vbm']['energy']
            # plot bandgap %
            xvbm = xkpt[cv['vbm']['index'][1]]
            xcbm = xkpt[cv['cbm']['index'][1]]
            Ecbm = cv['cbm']['energy']-cv['vbm']['energy']+BAND_SHIFT
            plt.scatter([xvbm],[0],color='r',s=40)
            plt.plot([max(0,xcbm-xkpt[-1]/100),min(xkpt[-1],xcbm+xkpt[-1]/100)],[Ecbm,Ecbm],color='r') 
            plt.plot([xcbm,xcbm],[0,Ecbm],c='r',lw=2)
            xtext=[xcbm+xkpt[-1]/100,xcbm-xkpt[-1]/6][xcbm>xkpt[-1]*2/3]
            plt.text(xtext,Ecbm/2,'{:.3f} eV'.format(Ecbm))
        else:
            shift = bf.get_fermi()
        
        for bands_ispin in bands:
            ybands = bands_ispin[...,0] - shift
            if BAND_SHIFT != 0:
                ybands[:,cv['vbm']['index'][0]:] += BAND_SHIFT
            plt.plot(xkpt,ybands,c=next(color))

        plt.axhline(c='r', linestyle='--')
        plt.xlim(0,xkpt[-1])
        plt.ylim(BAND_EMIN,BAND_EMAX)
        plt.ylabel(BAND_YLABEL)

    def plot_dos(self, path=None, job='pdos'):
        fig = Figure().figure(job)
        color = fig.set_color()

        # linestyles={'s':':','p':'-','d':'--','f':'-.'}
        df = DosFinder(path)
        if job == 'pdos':
            dos_energy,dos=df.get_ldos()
        elif job == 'tdos':
            dos_energy,dos=df.get_tdos()

        # initial plt setting %
        atominfo = df.atominfo(df.stdin)
        dos_energy -= (df.get_vbm() + df.get_fermi())/2 - DOS_SHIFT
        imin,imax = sum(dos_energy<DOS_EMIN),sum(dos_energy<DOS_EMAX)
        dos_energy = dos_energy[imin:imax]
        dos = dos[...,imin:imax] / df.volume(df.stdin) 

        limit = DOS_LIMIT
        if df.spin == 2:
            _limit = -limit
        else:
            _limit = 0

        if fig.group == None:
            plt.ylim(_limit,limit)
            plt.xlim(DOS_EMIN,DOS_EMAX)
            plt.axvline(c='r',linestyle='--')
            plt.xlabel(DOS_XLABEL)
            plt.ylabel(DOS_YLABEL)
        else:
            plt.xlim(_limit,limit)
            plt.ylim(DOS_EMIN,DOS_EMAX)
            plt.axhline(c='r',linestyle='--')
            #plt.xlabel("${}$".format(job.upper()))
            plt.gca().yaxis.tick_right()

        # plot %
        if job == 'pdos':
            tmp = 0
            for element,num in atominfo:
                dos_atom = np.sum(dos[tmp:tmp+num,:,:],axis=0)
                tmp += num
                if df.spin == 1:
                    for k in range(3):
                        if max(dos_atom[k]) < 0.003: continue
                        x,y = fig.set_axis(dos_energy, dos_atom[k])
                        plt.plot(x,y,label=element+'-'+df.orbits[k])
         
                elif df.spin == 2:
                    plt.axhline(linewidth=1,color='black',linestyle='--')
                    for s,dos_data in zip(['up','down'],dos_atom):
                        for k in range(len(df.orbits)):
                            if max(np.abs(dos_data[k])) < 0.003: continue
                            x,y = fig.set_axis(dos_energy, dos_data[k])
                            label = '{0}-{1}$\{2}arrow$ '.format(element,df.orbits[k],s)
                            plt.plot(x,y,label=label)

        elif job == 'tdos':
            if df.spin == 1:
                x,y = fig.set_axis(dos_energy, dos)
                plt.plot(x,y)
            elif df.spin == 2:
                plt.axhline(linewidth=1, color='black', linestyle='--')
                for s,dos_spin in zip(['up','down'],dos):
                    x,y = fig.set_axis(dos_energy, dos_spin)
                    plt.plot(x,y,label='spin-'+s)

        if job != 'tdos' or df.spin ==2: 
            plt.legend(loc=1)

    def plot_absorb(self,path, job='absorb'):
        import scipy.constants as sc
        fig = Figure().figure('absorb')
        color = fig.set_color()
        plt.axes(yscale='log')

        of = OpticsFinder(path)
        imag,real = of.get_dielectric_func_from_xml()
        comp=real[:,1:]+imag[:,1:]*(0+1j)
        energy=real[:,0]
        constant=sc.pi*np.sqrt(8)*sc.eV/sc.h/sc.c/100
        Absorb,Reflex=[],[]
        for i in range(len(energy)):
            var=comp[i]
            matrix=[[var[0],var[3],np.conj(var[5])],
                    [np.conj(var[3]),var[1],var[4]],
                    [var[5],np.conj(var[4]),var[2]]]
            w,v=np.linalg.eig(matrix)
            fa=lambda x:np.sqrt(np.abs(x)-np.real(x))*energy[i]*constant
            absorbs=[fa(n) for n in w]
            absorb_avg=np.mean(absorbs)*1e-4
            Absorb.append(absorb_avg)
         
            fn=lambda x:np.sqrt(0.5*(np.abs(x)+np.real(x)))
            ns=[fn(n) for n in w]
            n_avg=np.mean(ns)*1e-4
            Reflex.append(n_avg)
        if job == 'absorb':
            plt.plot(energy,Absorb,c='g')
        else:    # opttype == 'reflex':
            plt.plot(energy,Reflex,c='b')

        plt.ylim(1e-1,1e3)
        plt.xlim(ABSORB_EMIN,ABSORB_EMAX)
        plt.xlabel(ABSORB_XLABEL)
        plt.ylabel(ABSORB_YLABEL)


    def plot_dielfunc(self,path):
        fig = Figure().figure('dielectric')
        color = fig.set_color()
        of = OpticsFinder(path)
 
        # data reshape %
        imag,real = of.get_dielectric_func_from_xml()
        encut = np.sum(imag[:,0] > ABSORB_EMAX)
        energy = imag[:encut, 0]
        imag = imag[:encut, 3]
        real = real[:encut, 3]
        ymin = min(np.min(real), np.min(imag))*1.1
        ymax = max(np.max(real), np.max(imag))*1.1

        plt.xlim(0, ABSORB_EMAX)
        plt.ylim(ymin,ymax)
        plt.ylabel(DIEL_YLABEL)
        plt.xlabel(u'Energy (eV)')
        
        ax1 = plt.gca()
        l1 = ax1.plot(energy, imag, c='b', label='imag-z')
        ax2=ax1.twinx()
        l2 = ax2.plot(energy, real, c='g', label='real-z')
        plt.gcf().legend(loc=2,shadow=True,bbox_to_anchor=(0.14,0.94))
        plt.ylim(ymin,ymax)

    def plot_tdm(self,path=None):
        from jamip.analysis.vasp.wavecar import GrepWavecar
        from .convert import kpath2list

        fig = Figure().figure('tdm')

        # get kpath %
        bf = BandFinder(path)
        kpath=kpath2list(bf.kpath) 
        nkpt = bf.get_insert()
        kpoints = bf.get_kpoints()
        rec_vector = bf.get_info('reciprocal_lattice_vectors')

        # get dipole-mement from wavecar %
        w = GrepWavecar(bf.stdin)
        w.wavecar()
        pdms = w.get_dipole()
        tdms = np.sum(pdms,axis=1)

        # set x axis % 
        delta = [np.linalg.norm(np.dot(rec_vector,dk)) for dk in kpoints[1:]-kpoints[:-1] ]
        delta.insert(0,0)
        xkpt = np.cumsum(delta)
        xticks=[]
        for i in np.arange(0,len(kpoints)+1,nkpt):
            if i == len(kpoints): 
                i -= 1
            elif i > 0:
                tdms[i-1] = tdms[i] = np.mean(tdms[i-1:i+1])
            xticks.append(xkpt[i])
            plt.axvline(xkpt[i],c='black')
        ax = plt.gca()
        ax.set_xticks(xticks)
        ax.set_xticklabels(kpath)
        plt.plot(xkpt,tdms)
        plt.ylim(0, np.max(tdms)*1.1)
        plt.xlim(0,xkpt[-1])
        plt.ylabel(TDM_YLABEL)

    def plot_converge(self, path, job='cutoff'):
        from jamip.analysis.vasp.outcar import GrepOutcar
        from os.path import join, exists
        import re
  
        fig = Figure().figure('base')
        relax = join(path,'relax')
        energys = []
        times = []
 
        for dir in os.listdir(relax):
            values = re.findall('^%s-(\d+\.?\d*)' %job, dir)
            if len(values) and exists(join(relax, dir, 'OUTCAR')):
                value = float(values[0])
                try:
                    energy = GrepOutcar().free_energy(join(relax,dir))
                    energys.append([value, energy])
                except:
                    pass
                try:
                    cputime = GrepOutcar().cputime(join(relax,dir))
                    times.append([value, cputime])
                except:
                    pass
                
        if len(times) == 0:
            print('Warning! %s converge test for %s are all unfinished. ')
            raise
        
        energys = np.array(energys, dtype=float)
        energys = energys[np.argsort(energys[:,0])]
        times = np.array(times, dtype=float)
        times = times[np.argsort(times[:,0])]
        
        # plot energys % 
        plt.xticks(energys[:,0])
        if job == 'cutoff':
            plt.xlabel('E$_{cutoff}$ (eV)')
        elif job == 'kpoints':
            plt.xlabel('$kspacing$')
                    
        ax1 = plt.gca()
        ax1.plot(energys[:,0], energys[:,1], c='b')
        #ax1.tick_params(axis='y', colors='b')
        ax1.set_ylabel('Energy (eV)')#, color='b')
        #ax2=ax1.twinx()
        #ax2.plot(times[:,0], times[:,1], c='g')
        #ax2.tick_params(axis='y', colors='g')
        #ax2.set_ylabel('Cputime (s)', color='g')

    def plot_unfolding(self,path=None,**kwargs):
        from jamip.abtools.diyflow.unfolding import Unfolding
        Unfolding.plot(path)

    def plot_cohp(self,path,**kwargs):
        from jamip.abtools.diyflow.cohp import Cohp
        Cohp.plot(path)

    def plot_hseband(self,path,**kwargs):
        from jamip.abtools.diyflow.hse_band import Hse_band
        Hse_band.plot(path)

    @property
    def soft(self):
        return self._soft_

    @property
    def path(self):
        return self._path_

    @path.setter
    def path(self,value=None):
        from os.path import exists,join,isdir,relpath,abspath

        if not exists(value):
            raise OSError('PATH %s not exists !' %value)

        paths = []
        # single path %
        result = self.seek(value)
        if result != None:
            paths = [result]

        # mutil path %
        elif isdir(value):
            for dir in os.listdir(value):
                 result = self.seek(join(value,dir))
                 if result != None:
                     paths.append(result)

        self._path_ = paths
        # output plotpath %
        print("Total valid path = %d" %len(paths))

