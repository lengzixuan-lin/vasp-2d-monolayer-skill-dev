
# coding: utf-8
# Copyright (c) JUMP2 Development Team.
# Distributed under the terms of the JLU License.


#=================================================================
# This file is part of JAMIP.
#
# Copyright (C) 2017 Jilin University
#
#  JAMIP is a platform for high throughput calculation. It aims to
#  make simple to organize and run large numbers of tasks on the
#  superclusters and post-process the calculated results.
#
#  JAMIP is a useful packages integrated the interfaces for ab initio
#  programs, such as, VASP, Guassian, QE, Abinit and
#  comprehensive workflows for automatically calculating by using
#  simple parameters. Lots of methods to organize the structures
#  for high throughput calculation are provided, such as alloy,
#  heterostructures, etc.The large number of data are appended in
#  the MySQL databases for further analysis by using machine
#  learning.
#
#  JAMIP is free software. You can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published
#  by the Free sofware Foundation, either version 3 of the License,
#  or (at your option) and later version.
#
#  You should have recieved a copy of the GNU General Pulbic Lincense
#  along with JAMIP. If not, see <https://www.gnu.org/licenses/>.
#=================================================================
from .structure import Structure

"module to write the structure"
def write(structure,stdout=None,ftype=None,file=None):
    import os.path
    if ftype is None:
        if '.' in os.path.split(stdout)[-1]:
            ftype = os.path.split(stdout)[-1].split('.')[-1]

    if ftype == 'vasp':
        from jamip.abtools.vasp.vaspio import VaspIO
        if file is None: 
            stdout,file =os.path.split(os.path.abspath(stdout))
        VaspIO().write_poscar(structure,stdout,name=file)
    elif ftype == 'cif':
        from .io import write_cif
        if file is not None: 
            stdout = os.path.join(stdout,file)
        write_cif(structure,stdout)
 
"module to read the structure"

def read(name='POSCAR',ftype=None):
    """
    :param name: the input structure file;
    :return: object of Structure;
    """
    from .crystal import Read 
    import numpy as np

    obj = Structure()
    structure = Read(name,ftype).getStructure()

    obj.comment_line = structure['comment']
    obj.lattice = np.array(structure['lattice'])

    if structure['type'].lower() == 'direct':
        obj.direct = True
    elif structure['type'].lower() == 'cartesian':
        obj.direct = False 

    if 'constraints' not in structure or len(structure['constraints']) == 0:
        obj.select_dynamic = False
    else:
        obj.select_dynamic = structure['constraints']

    if 'velocities' not in structure or len(structure['velocities']) == 0:
        obj.initial_velocity = False
    else:
        obj.initial_velocity = structure['velocities'] 

    obj.species_of_elements = structure['elements']
    obj.number_of_atoms = structure['numbers']
    obj.atomic_positions = np.array(structure['positions'])

    return obj
