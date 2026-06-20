import os
import numpy as np
from .structure import Structure

def ziplist(alist):
    key,value = [],{}
    for i in alist:
       if i not in key:
           key.append(i)
           value[i] = 1
       else:
           value[i] += 1
    return key,[value[i] for i in key]

def phonopy2jamip(poscar):
    obj = Structure()
    obj.comment_line = 'PHONOPY'
    obj.lattice = np.asarray(poscar.cell)
    obj.direct = True
    obj.frozen = False
    elements,numbers = ziplist(poscar.symbols)
    obj.species_of_elements = elements
    obj.number_of_atoms = numbers
    obj.atomic_positions = np.asarray(poscar.scaled_positions)
    return obj

def jamip2phonopy(structure):
    from phonopy.structure.atoms import PhonopyAtoms
    lattice = structure.lattice
    positions = structure.get_positions()
    elements = structure.get_elements('symbol')
    unitcell = PhonopyAtoms(symbols=elements,cell = lattice,
                            scaled_positions=positions)
    return unitcell
