
__contributor__ = 'Kun Zhou'
#================================================================
# baisc method for control the input and output 
#================================================================

import os
import numpy as np

class QEIO(object):

    def write_structure(self, structure, fopen, direct=True, **kwargs):
        fopen.write('CELL_PARAMETERS angstrom\n')
        if abs(structure.scale_factor-1.0) > 1e-8:
            lattice = structure.lattice * structure.scale_factor
        else:
            lattice = structure.lattice 
        for l in lattice:
            fopen.write(' '.join('{0:>16.8f}'.format(c) for c in l))
            fopen.write('\n')

        if direct is True:
            fopen.write('ATOMIC_POSITIONS crystal\n')
            for i, p in enumerate(structure.atomic_positions):
                fopen.write('{0:>4}'.format(p.specie))
                fopen.write(' '.join('{0:>13.8f}'.format(j) for j in p.occupation.direct.xyz))
                #if structure.select_dynamic:
                #    fopen.write(' %5s %5s %5s' %p.freeze.xyz)
                fopen.write('\n')
        elif direct is False:
            fopen.write('ATOMIC_POSITIONS angstrom\n')
            for i, p in enumerate(structure.positions.cartesian):
                fopen.write('{0:>4}'.format(p.specie))
                fopen.write(' '.join('{0:>13.8f}'.format(j) for j in p.occupations.cartesian.xyz))
                #if structure.select_dynamic:
                #    fopen.write(' %5s %5s %5s' %p.freeze.xyz)
                fopen.write('\n')
        return fopen

    def write_potential(self, potential, fopen, **kwargs):

        fopen.write("ATOMIC_SPECIES\n")
        for pot in potential:
            fopen.write("{0[0]:6} {0[1]:>8}  {0[2]}\n".format(pot))
        return fopen

    def write_kpoints(self, fopen, **kwargs):

        from ..base.kpoints import __KPT__
        
        if self.model == 'Line Model':
            fopen.write("K_POINTS crystal_b\n")
            fopen.write("%d\n" %len(self.kpoints.kpath))
            fopen.write(self.kpoints.qeformat)
            
        elif self.model == 'Gamma':
            fopen.write("K_POINTS automatic\n")
            assert self.kpoints.size == 6
            fopen.write("  ".join(self.kpoints.astype(str).reshape(-1)))
            fopen.write("\n")

        elif self.model == 'Reciprocal':
            fopen.write("K_POINTS crystal\n")
            fopen.write(self.kpoints)

        return fopen

    def write_plot(self, incar, filename=None):

        if filename == None:
            filename = incar.name + '.plt.in'


        with open(filename,'w') as f:
            f.write("&%s\n" %incar.name)
            for key in ['prefix','outdir']:
                f.write("  %-15s = '%-s'\n" %(key.lower(),incar.pop(key)))

            for key,value in incar.items():
                if 'fil' in key:
                    value = "'%s'" %value
                f.write("  %-15s = %-s\n" %(key.lower(),value))
            f.write("/\n")
        return filename

    def write_pwscf(self, pwscfin, fopen, **kwargs):
        
        from .utils import pwscf_format

        fopen.seek(0,0)
        content = fopen.read()
        fopen.seek(0,0)
        #assert isinstance(system,PwscfIn) == True
        control, system, electrons, ions, cell = pwscf_format(pwscfin)
        print(pwscfin)

        fopen.write("&CONTROL\n")
        for key,value in control.items():
            fopen.write("  %-15s = %-s\n" %(key.lower(),value))
        fopen.write("/\n")

        fopen.write("&SYSTEM\n")
        for key,value in system.items():
            fopen.write("  %-15s = %-s\n" %(key.lower(),value))
        fopen.write("/\n")

        fopen.write("&ELECTRONS\n")
        for key,value in electrons.items():
            fopen.write("  %-15s = %-s\n" %(key.lower(),value))
        fopen.write("/\n")

        fopen.write("&IONS\n")
        for key,value in ions.items():
            fopen.write("  %-15s = %-s\n" %(key.lower(),value))
        fopen.write("/\n")

        fopen.write("&CELL\n")
        for key,value in cell.items():
            fopen.write("  %-15s = %-s\n" %(key.lower(),value))
        fopen.write("/\n")

        # rewrite %
        fopen.write(content)

        return fopen





            
        
