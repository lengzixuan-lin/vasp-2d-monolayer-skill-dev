import os
import numpy as np
from copy import deepcopy
from .structure import Structure

class Structure_operation(object):

    def __init__(self,structure=None):
        if isinstance(structure,Structure):
            self.structure = structure
        else:
            raise ("Sure you input a correct Structure class!")

    def init_structure(self,path):
        from jamip.structure import read
        self.structure = read(path)

    def write_poscar(self,obj,path):
        from jamip.abtools.vasp.vaspio import VaspIO
        if not isinstance(obj,Structure):
            raise ("Sure you input a correct Structure class!")
        io = VaspIO()
        io.write_poscar(obj,path)

    def update(self,comment=None,lattice=None,**kwargs):
        ''' the update attribute
             comment_line
             scale_factor
             species_of_elements
             number_of_atoms
             direct
             atomic_positions
             __dict__.keys()
        '''
        tmp = deepcopy(self.structure)
        if isinstance(comment,str):
            tmp.comment_line = comment
        if isinstance(lattice,np.ndarray):
            tmp.lattice = lattice
        else:
            print(lattice)
        return tmp

    def operation_lattice(self,axis,scales):
        comment = deepcopy(self.structure.comment_line)
        lattice = deepcopy(self.structure.lattice)
        operations = {}
        for scale in scales:
            tmp = {}
            key = axis+'_'+str(scale)
            tmp['comment'] = comment+'_'+key
            tmp['lattice'] = np.array(lattice)
            tmp['lattice'][0] = lattice[0]*scale
            operations[key] = tmp
        return operations

class Operation(Structure_operation):

    def __init__(self,func=None):
        if func: self.func=func

    def lattice(self,structure,axis,scale):
        if isinstance(structure,Structure):
            structure = [structure]
        if not isinstance(structure,list):
            raise ("wrong input when Operation structure") 
        new_struct = []
        new_path = []
        for struct in structure: 
            self.structure = struct
            operas = self.operation_lattice(axis,scale)
            for key,value in operas.items():
                new_path.append(key)
                new_struct.append(self.update(**value))
        return new_struct,new_path


if __name__ == "__main__":
    from jamip.structure import read
    path = os.getcwd()
    st1 = read("test/POSCAR")
    opera = Operation()
    structs = {}
    lattice = st1.lattice
    axis = 'x'
    scale = [0.98,0.99,1.01,1.02]
    new_structs,new_paths= opera.lattice(st1,axis,scale)
    for struct,path in zip(new_structs,new_paths):
        os.makedirs(path)
        opera.write_poscar(struct,path)


