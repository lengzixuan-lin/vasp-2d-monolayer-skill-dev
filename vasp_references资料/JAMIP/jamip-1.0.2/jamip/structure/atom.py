import numpy as np

__all__ = ['Cell', 'SelectDynamic', 'Position', 'Coord']
__contributor__ = 'xingang zhao, xingang.zhao@colorado.edu'

class SelectDynamic(object):
    """
    cls define the fronze of the atoms;
        Default:: not fronze x, y, z;
    """

    frozen_x = True 
    frozen_y = True 
    frozen_z = True 
    
    def __init__(self, frozen=None):
        if frozen is not None:
            self.frozen_x = frozen[0]
            self.frozen_y = frozen[1]
            self.frozen_z = frozen[2]
     
    @property
    def xyz(self):
        return (self.frozen_x, self.frozen_y, self.frozen_z)
   
    def __repr__(self):
        s= "%s" % ([self.frozen_x, self.frozen_y, self.frozen_z])
        return s


class Cell(object):

    """
    cls Lattice aim to define the lattice vector. 
   
    properties:
        length a, b, c; 
        angle alpha, beta, gamma; 
        cell volume; 
        scale: scale lattice vectors;
        vectors: 3x3 numpy.array; 
   function:
        get_cell: return self.vectors, i.e., 3x3 vectors;	 
    """

    def __init__(self, cell, scale=1.0):
        
        self.__scale = scale
        self.__cell = np.array(np.float64(cell))*self.__scale 
   
    @property
    def a(self):
        return np.linalg.norm(self.__cell[0])

    @property
    def b(self):
        return np.linalg.norm(self.__cell[1])

    @property
    def c(self):
        return np.linalg.norm(self.__cell[2])

    @property
    def alpha(self):
        value=np.dot(self.__cell[0],self.__cell[1])/(self.a*self.b)
        return np.arccos(value)/np.pi*180

    @property
    def beta(self):
        value=np.dot(self.__cell[1],self.__cell[2])/(self.b*self.c)
        return np.arccos(value)/np.pi*180

    @property
    def gamma(self):
        value=np.dot(self.__cell[0],self.__cell[2])/(self.a*self.c)
        return np.arccos(value)/np.pi*180
    
    @property
    def volume(self):
        return np.abs(np.dot(np.cross(self.__cell[0],self.__cell[1]),self.__cell[2]))

    @property     
    def vectors(self):
        return np.array(self.__cell, dtype=float)
	
    @property 
    def scale(self):
        return self.__scale

    @scale.setter
    def scale(self, value=1.0):
        if np.issubdtype(type(value), np.number):
           self.__scale = float(value)
           self.__cell = self.__cell*value

    @property
    def reciprocal(self):
        return self.vectors.I 

    def __repr__(self):
        s=''
        if self.__cell is not None:
            s = "lattice info:\n"
            s += " length    a (A) : %f\n" % (self.a)  
            s += " length    b (A) : %f\n" % (self.b)  
            s += " length    c (A) : %f\n" % (self.c)  
            s += " cell volume(A^3): %f\n" % (self.volume)  
            s += " lattice vectors:\n"
            s += ' '.join("%7.4f" % (v) for v in self.__cell[0])+'\n'
            s += ' '.join("%7.4f" % (v) for v in self.__cell[1])+'\n'
            s += ' '.join("%7.4f" % (v) for v in self.__cell[2])+'\n'

        return s

class Position(object):
    """
    atomic position % 
    """
    x = 0.0
    y = 0.0
    z = 0.0
    def __init__(self, coord=None):
        self.x = coord[0]
        self.y = coord[1]
        self.z = coord[2]
        self.xyz = np.float64(coord)

    def __repr__(self):
        return "%s\n" % ([self.x, self.y, self.z])

class Coord(object):

    """
    cls type of coordination of atoms.
    """
    def __init__(self, coord=None):
        self.__position = coord

    @property 
    def direct(self):
        return Position(self.__position[0])

    @direct.setter
    def direct(self, value=None):
        if value is not None:
            self.__position[0]=np.array(value) 

    @property
    def cartesian(self):
        return Position(self.__position[1])
    
    @cartesian.setter
    def cartesian(self, value=None):
        if value is not None:
            self.__position[1]=np.array(value) 
    
    def __repr__(self):
        s= "Direct:["
        for v in self.__position[0]:
            s += "{0:>12.8f}".format(v)
        s += "]" 
        return s  
    
class Atom(object):
    """
    cls to define one position, including,
          element
          occupied coordination 
          charge 
          magnetic
          constraint
    """ 
    def __init__(self, element=None, position=None, cell=None, magnetic=None,\
                 freeze=None, velocity=None, direct=True, *args, **kwargs):
	
        # freeze the atom or not %
        self.__specie = element
        self.__occup =  position
        self.__freeze = freeze 
        self.__velocity = velocity
        self.__magnetic = magnetic 
        self.__direct = direct
        self.__cell = cell

    # for elemenets %
    @property
    def specie(self):
        return self.__specie

    @specie.setter
    def specie(self, value=None):
        if isinstance(value,str):
            self.__specie = value 

    # occupied coordination %         
    @property
    def occupation(self):
        """
        return an object of position 
        """
        occ = np.array(self.__occup)

        if self.__direct is True:
            tmp = [occ, np.matrix(occ)*self.__cell]
        else:
            tmp = [np.array(np.matrix(occ)*np.linalg.inv(self.__cell))[0], occ]

        return Coord(tmp)

    @occupation.setter
    def occupation(self, value=None):
        self.__occup = value

# ========================================================
#       occ = None
#       if value is None:
#           value = self.__occup 
#       if isinstance(value, list):
#           occ =np.array(value) 
#       if isinstance(value, Coord):
#           occ =value.xyz
#       if self.__direct is True:
#           tmp = [occ, np.matrix(occ)*self.__cell]
#       else:
#           tmp = [np.array(np.matrix(occ)*self.__cell.I)[0], occ]
#
#       self.__occup = Coord(tmp)
# =========================================================

    # magnetic % 
    @property 
    def magnetic(self):
        return self.__magnetic

    @magnetic.setter
    def magnetic(self, value=None):
        if value is not None:
            self.__magnetic = value  

# ===========================================================    
#    # charge %   
#    @property 
#    def charge(self):
#        return self.__charge 
#    
#    @charge.setter
#    def charge(self, charge=None):
#        if charge is not None:
#            self.__charge = charge 
# =========================================================
      
    # freeze x/y/z % 
    @property  
    def freeze(self):
        return SelectDynamic(self.__freeze)
    
    @freeze.setter
    def freeze(self, value=None):
        if isinstance(value, bool):
            self.__freeze = np.array([value]*3,dtype=bool)
        elif isinstance(value,list) or isinstance(value,np.ndarray):
            if len(value == 1):
                self.__freeze = np.array([value[0]]*3,dtype=bool)
            if len(value == 3):
                self.__freeze = np.array(value,dtype=bool)
        elif isinstance(value,SelectDynamic):
            self.__freeze = np.array(value.xyz,dtype=bool)
 
    @property  
    def velocity(self):
        return np.array(self.__velocity)
    
    @velocity.setter
    def velocity(self, value=None):
        self.__velocity = value

    def __repr__(self):
        s = ''
        s += "(Element: %s, Position: %s" \
               % (self.specie, self.occupation)
        if self.__freeze is not None: s += ", Freeze: %s" % (self.freeze) 
        if self.__velocity is not None: s += ", Velocity: %s" % (self.velocity) 
        #if self.__charge is not None: s += ", Charge: %s" % (self.charge)
        if self.__magnetic is not None: s += ", Magnetic: %s" % (self.magnetic)
        s += ")"   
        return s 
        
