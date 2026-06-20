# -*- coding: utf-8 -*-
import __future__ 

from .atom import Atom, Cell 
import numpy as np
#from operation import StructureOperation

#class Structure(StructureOperation):
class Structure(object):
    """
    define a crystal structure or molecule, including,
    
    Attributes:
        species_of_elements: list, sepcies of elements;
        number_of_atoms:     list, numbers of species;
	atomic_positions:    list, atomic position defined by Atom Object;
	comment_line:        string, introduction of structure;
        scale_factor:        float, default, 1.0;
        lattice:             numpy.array(3x3), default, None;   	 
	select_dynamic:      bool, default, False;  
	direct_coord:        bool, default. True;
    """

    magnetic = None 

    def __init__(self, *args, **kwargs):
	
        self.__comment = None
        self.__cell = None
        self.__scale = 1.0
        self.__positions = None
        self.__number = None
        self.__species = None
        self.__frozen = False
        self.__velocities = False
        self.__direct = True
        super(Structure, self).__init__()
	
    @property
    def comment_line(self):
        return self.__comment 

    @comment_line.setter
    def comment_line(self, value=None):
        self.__comment = value

    @property
    def scale_factor(self):
         return self.__scale 

    @scale_factor.setter
    def scale_factor(self, value=1.0):
        self.__scale = value

    @property
    def lattice(self):
        """
        Return:
            lattice parameters [[x1,x2,x3],[y1,y2,y3],[z1,z2,z3]].
        """
        return self.__cell.vectors

    @lattice.setter
    def lattice(self, value=None):
        self.__cell = Cell(value)

    @property
    def lattice_parameters(self):
        """
        Return:
            lattice parameters [a, b, c, alpha, beta, gamma].
        """
        va = self.__cell.vectors[0]
        vb = self.__cell.vectors[1]
        vc = self.__cell.vectors[2]

        a=np.linalg.norm(va)
        b=np.linalg.norm(vb)
        c=np.linalg.norm(vc)
        alpha=np.degrees(np.arccos(np.clip(np.dot(vb/b, vc/c), -1, 1)))
        beta =np.degrees(np.arccos(np.clip(np.dot(va/a, vc/c), -1, 1)))
        gamma=np.degrees(np.arccos(np.clip(np.dot(va/a, vb/b), -1, 1)))
        return np.array([a,b,c,alpha,beta,gamma])

    @property
    def species_of_elements(self):
        return self.__species
    
    @species_of_elements.setter
    def species_of_elements(self, value=None):
        self.__species = value

    @property
    def number_of_atoms(self):
        return self.__number

    @number_of_atoms.setter
    def number_of_atoms(self, value=None):
        self.__number = value

    @property 
    def select_dynamic(self):

        return False if self.__frozen is False else True

    @select_dynamic.setter
    def select_dynamic(self, value=False):
        self.__frozen = False
        if isinstance(value,np.ndarray) or isinstance(value,list):
            self.__frozen = np.array(value)

            if self.__positions != None and len(self.__positions) == len(value):
                self.atomic_positions = self.__atomic_coord

    @property
    def initial_velocity(self):

        return False if self.__velocities is False else True

    @initial_velocity.setter
    def initial_velocity(self, value=False):
        self.__velocities = False
        if isinstance(value,np.ndarray) or isinstance(value,list):
            self.__velocities = np.array(value)

            if self.__positions != None and len(self.__positions) == len(value):
                self.atomic_positions = self.__atomic_coord

    @property
    def direct(self):
        return self.__direct
     
    @direct.setter 
    def direct(self, value=True):
        self.__direct = value

    @property 
    def atomic_positions(self):
        return self.__positions

    @atomic_positions.setter
    def atomic_positions(self, value=None):
        positions =  []
        elements = self.get_elements(type='symbol')
        frozen = [None]*len(elements)
        velocities = [None]*len(elements)

        if self.select_dynamic == True:
            frozen = self.__frozen

        if self.initial_velocity == True:
            velocities = self.__velocities

        if not len(elements) == len(value) == len(frozen) == len(velocities):
            raise ValueError('''
            Atoms NUMBER NOT CONSISTENT:
                  NATOMS -> %d
                 NCOORDS -> %d
                  FROZEN -> %d
                VELOCITY -> %d       
            ''' %(len(elements), len(value), len(frozen), len(velocities)))

        for i, atom in enumerate(value):
            positions.append(Atom(elements[i],atom,
                                  cell=self.__cell.vectors, 
                                  freeze=frozen[i], 
                                  velocity=velocities[i],
                                  direct=self.__direct))

        self.__atomic_coord = np.asarray(value)
        self.__positions = positions
        del positions

    def bandStructure(self):
        return (self.lattice, self.__atomic_coord, self.get_elements())

    @classmethod
    def create_from_cell(cls, cell, comment='jamip'):
        assert len(cell) == 3
        lattice, positions, elements = cell
        obj = cls()
        obj.comment_line = comment
        obj.lattice = lattice
        obj.direct = True
        species,numbers = cls.elements2species(elements) 
        obj.species_of_elements = species
        obj.number_of_atoms = numbers
        obj.atomic_positions = positions
        return obj

    @classmethod
    def elements2species(cls,elements):
        from .atomic_number import atomic
        species = {}
        for elm in elements:
            if elm not in species:
                species[elm] = 1
            else:
                species[elm] += 1
        if isinstance(elements[0],int) or np.issubdtype(type(elements[0]),np.number):
            elements = []
            for elm in species:
                elements.append(atomic[elm])
            elements = np.array(elements) 
        else:
            elements = np.array(list(species.keys()))
        numbers = np.array(list(species.values()))
        return elements,numbers

    def get_format(self,divisor=False,split=''):
        div = 1
        if divisor is True:
            div = np.gcd.reduce(self.__number)
        format = ''
        for i,e in enumerate(self.__species):
            if self.__number[i]/div != 1:
                format += '%s%d%s' %(e,self.__number[i]/div,split)
            else:
                format += '%s%s' %(e,split)
        return format.rstrip(split)

    def get_formula_units_Z(self):
        return np.gcd.reduce(self.__number)

    def get_volume(self):
        return np.linalg.det(self.lattice)

    # elements fit for some pkgs
    def get_elements(self,type='number'):
        from .atomic_number import number
        elements = []
        if type == 'symbol':
            for i,e in enumerate(self.__species):
                elements.extend([e]*self.__number[i])
        elif type == 'number':
            for i,e in enumerate(self.__species):
                elements.extend([number[e]]*self.__number[i])
        return elements

    def get_positions(self):
        return self.__atomic_coord 

    def get_all_distances(self, min=False):
        tot = sum(self.__number)
        distances = np.zeros((tot,tot))
        for kernel,atom1 in enumerate(self.__atomic_coord):
            for bonding,atom2 in enumerate(self.__atomic_coord):
                if kernel == bonding : continue
                if min:
                    rec = [i-round(i) for i in atom1-atom2]
                else:
                    rec = atom1-atom2
                distance = np.dot(rec,self.__cell.vectors)
                distances[kernel][bonding] = np.linalg.norm(distance)
        return distances
