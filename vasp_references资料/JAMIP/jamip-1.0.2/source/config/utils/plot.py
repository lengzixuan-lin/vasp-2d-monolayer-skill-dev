# Plot params

BAND_EMIN = -2
BAND_EMAX = 4
BAND_SHIFT = 0
BAND_XLABEL = '' 
BAND_YLABEL = 'Energy (eV)'

DOS_EMIN = -2
DOS_EMAX = 4
DOS_LIMIT = 0.04
DOS_XLABEL = 'Energy (eV)'
DOS_YLABEL = '$PDOS\ (states/eV/\AA^{3})$'

# Supported Plot Functions
# VASP.electric : band, fatband, hseband, pdos, tdos, cohp, tdm, unfolding
# VASP.optics   : absorb, dielectric
# VASP.phonon   : phband, phdos, gruneisen, softmode
# QE.electric   : band, tdos

if __name__ == '__main__':
    # from jamip.utils.qeplot import QEPlot
    from jamip.utils.plot import Plot
    pl = Plot(path='Results/Si.vasp')
    #pl.plots('band')
    pl.plots('fatband')
    #pl.plots('pdos')
    #pl.plots('unfolding')

