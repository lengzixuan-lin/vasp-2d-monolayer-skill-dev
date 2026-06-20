from jamip.analysis.vasp import PhononFinder
from jamip.utils.plot import Figure
import matplotlib.pyplot as plt
import numpy as np

BAND_EMAX = 3
BAND_SHIFT = 0
BAND_XLABEL = ''
BAND_YLABEL = 'Energy (eV)'

DOS_EMIN = -1
DOS_EMAX = 3
DOS_LIMIT = 0.04
DOS_XLABEL = 'Energy (eV)'
DOS_YLABEL = '$PDOS\ (states/eV/\AA^{3})$'

MESH = [10,10,10]

try:
    from plot import *
except:
    raise OSError("The plotting program name can only be plot.py ! ")
class PhononPlot:

    dim = None
    overwrite = False

    def softmode(self,path):

        Figure().figure('base')

        pf = PhononFinder(path)
        dat = []
        for key,value in pf.get_softmode_result().items():
            dat.append([key[4:],value])
       
        dat = np.array(dat,dtype=float)
        dat = dat[np.argsort(dat[:,0],axis=0)]
        dat[:,1] -= dat[0,1]
        yrange = np.max(dat[:,1]) - np.min(dat[:,1])
        magnitudes = np.floor(np.log10(yrange))
        mult = np.power(10,magnitudes)
        if yrange / mult < 5:
            mult /= 2
       
        plt.plot(dat[:,0]*0.5,dat[:,1])
        plt.xlim(0,3)
        plt.xlabel('amplitude')
        plt.ylabel('Energy (eV)')
        plt.gca().yaxis.set_major_locator(plt.MultipleLocator(mult))
        plt.grid(linestyle='-.')
        plt.title('softmode')

    def band(self, path):
        from phonopy.phonon.band_structure import get_band_qpoints_and_path_connections
        from phonopy.file_IO import parse_FORCE_SETS
        from jamip.utils.convert import kpath2list
        from jamip.utils.brillouin_zone import HighSymmetryKpath
        from jamip.structure.atomic_number import number
        from os.path import exists, join

        fig = Figure().figure('band')
        color = fig.set_color()

        # structure %
        pf = PhononFinder(path)
        unitcell = pf.get_unitcell()
        phonon = pf.get_phonon()

        # get kpath %
        symbols = [number[i] for i in unitcell.symbols]
        cell = (unitcell.cell, unitcell.scaled_positions, symbols)
        bz = HighSymmetryKpath()
        kpoint = bz.get_HSKP(cell)
 
        paths = [[kpoint['Kpoints'][i] for i in p] for p in kpoint['Path']]
        kpath = kpoint['Path']
        qpoints, connections = get_band_qpoints_and_path_connections(paths, npoints=51)
        
        # update force %
        file = join(pf.stdin, 'FORCE_SETS')
        if self.overwrite is True or not exists(file):
            forces = pf.get_forces()
            pf.write_forces(phonon, forces, file)

        force_sets=parse_FORCE_SETS(filename=file)
        phonon.set_displacement_dataset(force_sets)
        phonon.produce_force_constants(calculate_full_force_constants=False)
        phonon.run_band_structure(qpoints, path_connections=connections, labels=kpath)
       
        max_freq = max([np.max(fq) for fq in phonon._band_structure.frequencies])
        max_dist = phonon._band_structure.distances[-1][-1]
        xscale = max_freq / max_dist * 1.5
        distances_scaled = [d * xscale for d in phonon._band_structure.distances]
        spts = [p[0] for p in distances_scaled]
        spts.append(distances_scaled[-1][-1])
       
        plt.figure(figsize=(6,6),dpi=144)
        plt.title('Phonon Spectrum', pad=0.1, fontsize=14)
        plt.ylabel('Frequency (THz)')
        plt.axhline(linestyle='--',linewidth=1.5,color='green')
        plt.xlim(0,spts[-1])
        ax = plt.gca()
        ax.xaxis.set_tick_params(which='both', direction='in')
        ax.yaxis.set_tick_params(which='both', direction='in')
       
        ax.set_xticks(spts)
        ax.set_xticklabels(kpath2list(kpath))
       
        for i, (d, f, c) in enumerate(zip(distances_scaled, phonon._band_structure.frequencies, phonon._band_structure.path_connections)):
            curves = plt.plot(d, f, c='r')
            plt.axvline(d[0], linewidth=1, c='black', alpha=0.5)

    def dos(self, path, project=False):
        from phonopy.phonon.band_structure import get_band_qpoints_and_path_connections
        from phonopy.file_IO import parse_FORCE_SETS
        from os.path import exists, join

        fig = Figure().figure('dos')
        color = fig.set_color()

        # structure %
        pf = PhononFinder(path)
        unitcell = pf.get_unitcell()
        phonon = pf.get_phonon()

        # update force %
        file = join(pf.stdin, 'FORCE_SETS')
        if self.overwrite is True or not exists(file):
            forces = pf.get_forces()
            pf.write_forces(phonon, forces, file)

        force_sets=parse_FORCE_SETS(filename=file)
        phonon.set_displacement_dataset(force_sets)
        phonon.produce_force_constants(calculate_full_force_constants=False)
        phonon.run_mesh(mesh=MESH,is_mesh_symmetry=False,with_eigenvectors=True)
        phonon.run_projected_dos(xyz_projection=project)
        #volume = np.linalg.det(unitcell.cell)
       
        ax = plt.gca()
        ax.xaxis.set_tick_params(which='both', direction='in')
        ax.yaxis.set_tick_params(which='both', direction='in')
        # get range %
        energy = phonon._pdos.frequency_points 
        imin = sum(energy<DOS_EMIN)
        imax = sum(energy<DOS_EMAX)
        energy = energy[imin:imax]
       
        edos = {}
        if len(unitcell.symbols) == len(phonon._pdos.partial_dos):
            for elm,dos in zip(unitcell.symbols,phonon._pdos.partial_dos):
                if elm not in edos:
                    edos[elm] = []
                edos[elm].append(dos)
            for elm,dos in edos.items():
                dos = np.sum(dos,axis=0)[imin:imax]
                plt.plot(energy, dos, label=elm)
       
        elif len(unitcell.symbols)*3 == len(phonon._pdos.partial_dos):
            for i, elm in enumerate(unitcell.symbols):
                if elm not in edos:
                    edos['%s-x' %elm] = []
                    edos['%s-y' %elm] = []
                    edos['%s-z' %elm] = []
                edos['%s-x' %elm].append(phonon._pdos.partial_dos[i*3])
                edos['%s-y' %elm].append(phonon._pdos.partial_dos[i*3+1])
                edos['%s-z' %elm].append(phonon._pdos.partial_dos[i*3+2])
       
            for elm,dos in edos.items():
                dos = np.sum(dos,axis=0)[imin:imax]
                plt.plot(energy, dos, label=elm)
                #dos = np.sum(dos,axis=0)
                #plt.plot(phonon._pdos.frequency_points,
                #         dos, label=elm)
       
        if fig.group == None:
            plt.xlim(DOS_EMIN,DOS_EMAX)
            plt.axvline(c='r',linestyle='--')
        else:
            plt.ylim(DOS_EMIN,DOS_EMAX)
            plt.axhline(c='r',linestyle='--')

        plt.title('Density of Phonon States', pad=1)
        plt.xlabel('Frequency (THz)')
        plt.legend()

    def gruneisen(self, path):
         
        fig = Figure().figure('base')

        # structure %
        pf = PhononFinder(path)
        gruneisen = pf.get_gruneisen(self.overwrite)
        gruneisen.set_mesh(MESH)
        mesh = gruneisen._mesh
        # plt = gruneisen.plot_mesh()
        ax = plt.gca()
        ax.xaxis.set_ticks_position('both')
        ax.yaxis.set_ticks_position('both')
        ax.xaxis.set_tick_params(which='both', direction='in')
        ax.yaxis.set_tick_params(which='both', direction='in')

        n = len(mesh._gamma.T) - 1
        for i, (g, freqs) in enumerate(zip(mesh._gamma.T, mesh._frequencies.T)):
            color = (1. / n * i, 0, 1./ n * (n - i))
            plt.plot(freqs, g, 'o', color=color)

        plt.xlabel('Frequency (THz)')
        plt.ylabel('gruneisen')
