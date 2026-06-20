# -*- coding: utf-8 -*-
#!/usr/bin/env python3

from ..utils.variables import default_constants
        

class StructureAnalyser(object):
    
    def __init__(self, structure):
        """
        Arguments:
            structure: structure's object.
        """
        self.structure=structure
    
    def niggli_reduce(self, eps=1e-5):
        """
        Niggli reduction.
        
        Arguments:
            eps (default=1e-5): tolerance parameter, but unlike symprec the unit is not a length.
                This is used to check if difference of norms of two basis vectors 
                is close to zero or not and if two basis vectors are orthogonal
                by the value of dot product being close to zero or not. The detail
                is shown at https://atztogo.github.io/niggli/.
        
        Returns:
            Niggli reduction.
        """
        import spglib
        
        cell=self.structure.formatting('cell')
        lattice=cell['lattice']
        niggli_lattice=spglib.niggli_reduce(lattice, eps=eps)
        return niggli_lattice
    
    def delaunay_reduce(self, eps=1e-5):
        """
        Delaunay reduction.
        
        Arguments:
            eps (default=1e-5): tolerance parameter, see niggliReduce.
        """
        import spglib
        
        cell=self.structure.formatting('cell')
        lattice=cell['lattice']
        delaunay_lattice=spglib.delaunay_reduce(lattice, eps=eps)
        return delaunay_lattice
    
    def _calculate_RDF(self, formated_atom, max_r=10.0, min_r=default_constants.precision.value, dr=0.1, **kwargs):
        """
        radius distribution function (RDF) for atom.
        
        Arguments:
            max_r (default=10.0): max radius (unit: Angstrom).
            min_r (default=1e-3): min radius (unit: Angstrom).
            dr (default=0.1): delta radius (unit: Angstrom).
            
            kwargs:
                dtype (default=None): None or 'symbol_of_element'
            
        Returns:
            {r:{symbol:positions}}
        """
        import math
        import numpy as np
        from collections import OrderedDict
        from ..utils.convert import any2cartesian
        
        atom0=self.structure.get_atom(formated_atom=formated_atom) # center
        if atom0 is None:
            raise ValueError('non-existed formated_atom')
            
        dtype=None
        if 'dtype' in kwargs:
            dtype=kwargs['dtype']
        
        lattice_parameters=self.structure.lattice_parameters
        a_l=int(math.floor(atom0.position[0]-max_r/lattice_parameters[0])) # left of a in lattice for supercell
        a_r=int(math.ceil(atom0.position[0]+max_r/lattice_parameters[0])) # right of a in lattice for supercell
        b_l=int(math.floor(atom0.position[1]-max_r/lattice_parameters[1])) # left of b in lattice for supercell
        b_r=int(math.ceil(atom0.position[1]+max_r/lattice_parameters[1])) # right of b in lattice for supercell
        c_l=int(math.floor(atom0.position[2]-max_r/lattice_parameters[2])) # left of c in lattice for supercell
        c_r=int(math.ceil(atom0.position[2]+max_r/lattice_parameters[2])) # right of c in lattice for supercell
        dim=[[a_l, a_r], [b_l, b_r], [c_l, c_r]] # range of suercell's size

        rdf={}
        atoms=list(self.structure.atoms)
        for atom1 in atoms:
            symbol=atom1.element.symbol
            position=atom1.position
            if (dtype is None) or (isinstance(dtype, str) and (symbol == dtype)) or ((isinstance(dtype, list) or isinstance(dtype, np.ndarray)) and (symbol in dtype)):
                for i in range(dim[0][0], dim[0][1]): # x
                    for j in range(dim[1][0], dim[1][1]): # y
                        for k in range(dim[2][0], dim[2][1]): # z
                            x=position[0]+i
                            y=position[1]+j
                            z=position[2]+k
                            position1=[x, y, z, 'Direct']
                            
                            r=np.linalg.norm(any2cartesian(self.structure.lattice, np.array(position1[:-1])-atom0.position)[:-1])
                            if dr > 10:
                                raise ValueError('beyond the upper boundary (< 10): dr')
                            elif dr >= 1:
                                r='{:d}'.format(math.floor(r/dr)*dr)
                            elif dr >= 0.1:
                                r='{:.1f}'.format(math.floor(r/dr)*dr)
                            elif dr >= 0.01:
                                r='{:.2f}'.format(math.floor(r/dr)*dr)
                            elif  dr >= 0.001:
                                r='{:.3f}'.format(math.floor(r/dr)*dr)
                            else:
                                raise ValueError('beyond the lower boundary (>= 0.001): dr')
                                
                            if min_r < float(r) <= max_r:
                                atom={symbol:[position1]}
                                if not(r in rdf.keys()):
                                    rdf[r]=atom
                                else:
                                    value=rdf[r] # {symbol: positions}
                                    if not(symbol in value.keys()):
                                        value[symbol]=atom[symbol]
                                    else:
                                        v=value[symbol]
                                        v.append(position1)
                                        value[symbol]=v
                                    rdf[r]=value

        rdf=OrderedDict(sorted(rdf.items(), key=lambda item:float(item[0])))
        
        return rdf
    
    def get_RDF_of_atom(self, formated_atom, max_r=10.0, min_r=default_constants.precision.value, dr=0.1, **kwargs):
        """
        radius distribution function (RDF) for atom.
        
        Arguments:
            max_r (default=10.0): max radius (unit: Angstrom).
            min_r (default=1e-3): min radius (unit: Angstrom).
            dr (default=0.1): delta radius (unit: Angstrom).
            
            kwargs:
                dtype (default=None): None or 'symbol_of_element'
            
        Returns:
            list-type [distance, number_of_atoms, [formated_atom1, formated_atom2,...],
                       ...
                      ]
        """
        dtype=None
        if 'dtype' in kwargs:
            dtype=kwargs['dtype']
            
        full_rdf=self._calculate_RDF(formated_atom=formated_atom, max_r=max_r, min_r=min_r, dr=dr, dtype=dtype)
        rdf=[] # [distance, number_of_atoms]}
        for key, value in full_rdf.items():
            distance=key
            number_of_atoms=0
            atoms=[]
            for key1, value1 in value.items():
                number_of_atoms += len(value1)
                for positon in value1:
                    atoms.append([key1]+positon)
            rdf.append([float(distance), number_of_atoms, atoms])
        return rdf
    
    def _calculate_RDF_of_all(self, max_r=10.0, min_r=default_constants.precision.value, dr=0.1):
        """
        get the radial distribution function (RDF) of all atom.
        """
        """
        radius distribution function (RDF) for atom.
        
        Arguments:
            max_r (default=10.0): max radius (unit: Angstrom).
            min_r (default=1e-3): min radius (unit: Angstrom).
            dr (default=0.1): delta radius (unit: Angstrom).

        Returns:
            {r:{symbol:positions}}
        """
        import math
        import numpy as np
        from collections import OrderedDict
        from ..utils.convert import any2cartesian
        
        lattice_parameters=self.structure.lattice_parameters
        atoms=list(self.structure.atoms)
        rdf={}
        for atom0 in atoms:
            a_l=int(math.floor(atom0.position[0]-max_r/lattice_parameters[0])) # left of a in lattice for supercell
            a_r=int(math.ceil(atom0.position[0]+max_r/lattice_parameters[0])) # right of a in lattice for supercell
            b_l=int(math.floor(atom0.position[1]-max_r/lattice_parameters[1])) # left of b in lattice for supercell
            b_r=int(math.ceil(atom0.position[1]+max_r/lattice_parameters[1])) # right of b in lattice for supercell
            c_l=int(math.floor(atom0.position[2]-max_r/lattice_parameters[2])) # left of c in lattice for supercell
            c_r=int(math.ceil(atom0.position[2]+max_r/lattice_parameters[2])) # right of c in lattice for supercell
            dim=[[a_l, a_r], [b_l, b_r], [c_l, c_r]] # range of suercell's size

            for atom1 in atoms:
                symbol=atom1.element.symbol
                position=atom1.position
                for i in range(dim[0][0], dim[0][1]): # x
                    for j in range(dim[1][0], dim[1][1]): # y
                        for k in range(dim[2][0], dim[2][1]): # z
                            index0=atoms.index(atom0)
                            index1=atoms.index(atom1)
                            if not((index1 <= index0) and (i == 0 and j == 0 and k == 0)):
                                x=position[0]+i
                                y=position[1]+j
                                z=position[2]+k
                                position1=[x, y, z, 'Direct']
                            
                                r=np.linalg.norm(any2cartesian(self.structure.lattice, np.array(position1[:-1])-atom0.position)[:-1])
                                if dr > 10:
                                    raise ValueError('beyond the upper boundary (< 10): dr')
                                elif dr >= 1:
                                    r='{:d}'.format(math.floor(r/dr)*dr)
                                elif dr >= 0.1:
                                    r='{:.1f}'.format(math.floor(r/dr)*dr)
                                elif dr >= 0.01:
                                    r='{:.2f}'.format(math.floor(r/dr)*dr)
                                elif  dr >= 0.001:
                                    r='{:.3f}'.format(math.floor(r/dr)*dr)
                                else:
                                    raise ValueError('beyond the lower boundary (>= 0.001): dr')
                                
                                if min_r < float(r) <= max_r:
                                    atom={symbol:[position1]}
                                    if not(r in rdf.keys()):
                                        rdf[r]=atom
                                    else:
                                        value=rdf[r] # {symbol: positions}
                                        if not(symbol in value.keys()):
                                            value[symbol]=atom[symbol]
                                        else:
                                            v=value[symbol]
                                            v.append(position1)
                                            value[symbol]=v
                                        rdf[r]=value

        rdf=OrderedDict(sorted(rdf.items(), key=lambda item:float(item[0])))

        return rdf
    
    def get_RDF_of_all(self, max_r=10.0, min_r=default_constants.precision.value, dr=0.1):
        """
        radius distribution function (RDF) for all atom.
        
        Arguments:
            max_r (default=10.0): max radius (unit: Angstrom).
            min_r (default=1e-3): min radius (unit: Angstrom).
            dr (default=0.1): delta radius (unit: Angstrom).
            
        Returns:
            list-type [distance, number_of_atoms, [formated_atom1, formated_atom2,...],
                       ...
                      ]
        """
        full_rdf=self._calculate_RDF_of_all(max_r=max_r, min_r=min_r, dr=dr)
        rdf=[] # [distance, number_of_atoms]}
        for key, value in full_rdf.items():
            distance=key
            number_of_atoms=0
            atoms=[]
            for key1, value1 in value.items():
                number_of_atoms += len(value1)
                for positon in value1:
                    atoms.append([key1]+positon)
            rdf.append([float(distance), number_of_atoms, atoms])
        return rdf
    
    def get_coordination_atoms_of_atom(self, formated_atom, cutoff=3.0):
        """
        get the coordination atoms of given atom.
        
        Arguments:
            cutoff (default=3.0): cutoff radius when calculating the coordiantion atoms.
            
        Returns:
            the coordination atoms of given atom. list-type [formated_atom1, formated_atom2,...]
        """        
        full_rdf=self.get_RDF_of_atom(formated_atom=formated_atom, max_r=cutoff)
        coordination_atoms=[]
        for v in full_rdf:
            if v[0] <= cutoff:
                coordination_atoms += v[2]
        coordination_atoms=sorted(coordination_atoms, key=lambda v:v[0])
        return coordination_atoms
    
    def get_coordination_number_of_atom(self, formated_atom, cutoff=3.0):
        """
        get the coordination number of given atom within the cutoff radius.
        """
        return len(self.get_coordination_atoms_of_atom(formated_atom=formated_atom, cutoff=cutoff))
    
    def get_averaged_coordination_number(self, symbol_of_element, cutoff=3.0):
        """
        get the averaged coordination number of given element.
        """
        # check
        atoms=self.structure.get_atoms_of_element(symbol=symbol_of_element)
        averaged_coordination_number=0.0
        for atom in atoms:
            averaged_coordination_number += len(self.get_coordination_atoms_of_atom(formated_atom=atom.to_formated_atom(), cutoff=cutoff))
        averaged_coordination_number /= len(atoms)
        return averaged_coordination_number    
    
    def get_atomic_packing_factor(self, atomic_radii):
        """
        get the atomic packing factor.
        """
        pass
    
    def get_tolerance_factor(self, r_a, r_b, r0):
        """
        get the Goldschmidt tolerance factor by given atomic radii.
        """
        pass
    
    def get_XRD_pattern(self, target_of_anode_material=''):
        """
        calculate XRD pattern.
        
        Arguments:
            target_of_anode_material: target of anode material. 
                Anode   Cr   Fe   Co   Cu   Mo   Ag
                K_alpha 2.29 1.94 1.79 1.54 0.71 0.56
        
        Return:
            XRD pattern.
        """
        pass
    
