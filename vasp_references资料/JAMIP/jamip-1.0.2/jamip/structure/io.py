from jamip.structure.structure import Structure
import time
import os

def write_cif(s1,stdout):
    a,b,c,alpha,beta,gamma = s1.lattice_parameters

    with open(stdout,'w') as f:
        f.write('data_create_by_jamip\n')
        f.write('_audit_update_record %s\n' %time.strftime("%Y-%m-%d", time.localtime()))
 
        f.write("_chemical_formula_structural '%s'\n" %s1.get_format(divisor=True,split=' '))
        f.write("_chemical_formula_sum '%s'\n" %s1.get_format(split=' '))
        f.write("_chemical_name_structure_type %s\n" %s1.get_format(divisor=True))
 
        f.write('_cell_length_a     %g\n' % a)
        f.write('_cell_length_b     %g\n' % b)
        f.write('_cell_length_c     %g\n' % c)
        f.write('_cell_angle_alpha     %g\n' % alpha)
        f.write('_cell_angle_beta      %g\n' % beta)
        f.write('_cell_angle_gamma     %g\n' % gamma)
        f.write('_cell_formula_units_Z %s\n' % s1.get_formula_units_Z())
        f.write("_symmetry_space_group_name_H-M 'P 1'\n")
        f.write('_symmetry_int_tables_number 1\n')
        f.write('loop_\n')
        f.write('_symmetry_equiv_pos_site_id\n')
        f.write('_symmetry_equiv_pos_as_xyz\n')
        f.write("1 'x, y, z'\n")
        f.write('loop_\n')
        f.write('_atom_site_label\n')
        f.write('_atom_site_type_symbol\n')
        f.write('_atom_site_symmetry_multiplicity\n')
        f.write('_atom_site_Wyckoff_symbol\n')
        f.write('_atom_site_fract_x\n')
        f.write('_atom_site_fract_y\n')
        f.write('_atom_site_fract_z\n')
        f.write('_atom_site_B_iso_or_equiv\n')
        f.write('_atom_site_occupancy\n')
        for e,pos in zip(s1.get_elements(type='symbol'),s1.get_positions()):
            f.write('{0} {0} 1 a {1[0]:.5f} {1[1]:.5f} {1[2]:.5f} . 1. \n'.format(e,pos))
