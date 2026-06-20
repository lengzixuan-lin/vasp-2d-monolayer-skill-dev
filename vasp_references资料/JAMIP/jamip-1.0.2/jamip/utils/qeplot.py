from jamip.utils.plot import Figure, Plot
import matplotlib.pyplot as plt
import numpy as np
import os

BAND_EMIN = -1
BAND_EMAX = 3
BAND_SHIFT = 0
BAND_XLABEL = ''
BAND_YLABEL = 'Energy (eV)'

DOS_EMIN = -1
DOS_EMAX = 3
DOS_LIMIT = 0.04
DOS_XLABEL = 'Energy (eV)'
DOS_YLABEL = '$PDOS\ (states/eV/\AA^{3})$'

try:
    from plot import *
except:
    raise OSError("The plotting program name can only be plot.py ! ")

class QEPlot(Plot):

    def plot_band(self, path):

        # Initializes the data retrieval module & pyplot & colormap %
        from jamip.analysis.qe import BandFinder
        from jamip.utils.convert import kpath2list
        fig = Figure().figure('band')
        color = fig.set_color()

        # grep main datas %
        bf = BandFinder(path)
        bands=bf.get_bands()
        kpoints = bf.get_kpoints()
        rec_vector = bf.get_rec_lattice()

        # set x axis % 
        delta = [np.linalg.norm(np.dot(rec_vector,dk)) for dk in kpoints[1:]-kpoints[:-1] ]
        delta.insert(0,0)
        xkpt = np.cumsum(delta)
        kpaths = bf.kpath
        xticks=[0]
        for i in bf.insert:
            xticks.append(xkpt[i])
            plt.axvline(xkpt[i],c='black')
        ax = plt.gca()
        ax.set_xticks(xticks)
        ax.set_xticklabels(kpath2list(kpaths))

        # add bandgap %
        cv = bf.get_cbmvbm(bands,kpoints)
        if cv['gap'] > 0:
            shift = cv['vbm']['energy']
            # plot bandgap %
            xvbm = xkpt[cv['vbm']['index'][1]]
            xcbm = xkpt[cv['cbm']['index'][1]]
            Ecbm = cv['cbm']['energy']-cv['vbm']['energy']+BAND_SHIFT
            plt.scatter([xvbm],[0],color='r',s=40)
            plt.plot([max(0,xcbm-xkpt[-1]/100),min(xkpt[-1],xcbm+xkpt[-1]/100)],[Ecbm,Ecbm],color='r')
            plt.plot([xcbm,xcbm],[0,Ecbm],c='r',lw=2)
            if xcbm>xkpt[-1]*2/3:
                plt.text(xcbm-xkpt[-1]/6,Ecbm/2,'{:.3f} eV'.format(Ecbm))
            else:
                plt.text(xcbm+xkpt[-1]/100,Ecbm/2,'{:.3f} eV'.format(Ecbm))
        else:
            shift = bf.get_fermi()

        ybands = bands[...,0] - shift
        if BAND_SHIFT != 0:
            ybands[:,cv['vbm']['index'][0]:] += BAND_SHIFT
        plt.plot(xkpt,ybands,c=next(color))
        plt.ylim(BAND_EMIN,BAND_EMAX)
        plt.xlim(0,xkpt[-1])

    def plot_dos(self, path, job):

        from jamip.analysis.qe import DosFinder
        from jamip.utils.convert import kpath2list
        fig = Figure().figure(job)
        color = fig.set_color()
  
        # get main data %
        df = DosFinder(path)
        if job == 'tdos':
            dos_energy,dos = df.get_tdos()
        if job == 'pdos':
            atominfo, dos_energy,dos = df.get_pdos()

        dos_energy -= df.get_vbm()
        imin,imax = sum(dos_energy<DOS_EMIN),sum(dos_energy<DOS_EMAX)
        dos_energy = dos_energy[imin:imax]
        dos = dos[...,imin:imax] / df.get_volume()

        limit = DOS_LIMIT
        if df.spin == 2:
            _limit = limit
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
            plt.xlabel("${}$".format(job.upper()))

        if job == 'tdos':
            if df.spin == 1:
                x,y = fig.set_axis(dos_energy, dos)
                plt.plot(x,y)
        elif job == 'pdos':
            for i,element in enumerate(atominfo):
                dos_atom = dos[i]
                if df.spin == 1:
                    for k in range(3):
                        if max(np.abs(dos_atom[k])) < 0.003: continue
                        x,y = fig.set_axis(dos_energy, dos_atom[k])
                        plt.plot(x,y,label=element+'-'+df.orbits[k])

        if job != 'tdos' or df.spin ==2:
            plt.legend(loc=1)

