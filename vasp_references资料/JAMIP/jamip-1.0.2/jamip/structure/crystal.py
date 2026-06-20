__all__=['Read','convert_value','parse_multiline_string','parse_singletag',
'parse_loop','parse_items','parse_block','parse_cif','format_symbol',
'equival_pos','numbers_cal','lattice_vector','SpacegroupError',
'SpacegroupNotFoundError','SpacegroupValueError']

import os 
import numpy as np
from sys import exit
class ReadError(Exception):
    pass
    
class Read(object):
    """
    reading structure
    
    arguments:
        file: path of structure. i.e. /home/xx/xx/POSCAR, POSCAR
        type: type of structure file. i.e. crystal: cif, poscar; molecule: xyz, mol....
    
    """
    
    def __init__(self, file, ftype=None):
        self.file=file
        
        if ftype == None:
            if self.file.endswith('.cif'):
                self.ftype='cif'
            elif self.file.endswith('.xyz'):
                self.ftype='xyz'
            elif self.file.endswith('.mol'):
                self.ftype='mol'
            elif self.file.endswith('.vasp'):
                self.ftype = 'poscar'
            elif self.file.endswith('.xml'):
                self.ftype = 'qe'
            elif self.file.endswith('.in'):
                self.ftype = 'qe'
            elif 'CONTCAR' in os.path.basename(self.file):
                self.ftype='poscar'
            elif 'POSCAR' in os.path.basename(self.file):
                self.ftype='poscar'
            else:
                raise ReadError('please specify the type of file')
        elif ftype == 'cif':
            self.ftype='cif'
        elif ftype.lower() == 'poscar':
            self.ftype='poscar'
        elif ftype.lower() == 'xyz':
            self.ftype='xyz'
        elif ftype.lower() == 'mol':
            self.ftype='mol'
        elif ftype.lower() == 'qe':
            self.ftype='qe'
        else:
            raise ReadError('unknown type of file!')
       
                    
    def getStructure(self):
        """
        read structure
        
        returns:
            json's object of a structure
            
        """
        if self.ftype == 'cif':
            return self.__readCIF()
        elif self.ftype == 'poscar':
            return self.__readPOSCAR()
        elif self.ftype == 'xyz':
            return self.__readXYZ()
        elif self.ftype == 'mol':
            return self.__readMOL()
        elif self.ftype == 'qe':
            return self.__readQE()

    def __readQE(self):
        """
        read QE.xml file

        returns:
            cif: A dictionary including:
                 lattice=[[x1,y1,z1],
                         [x2,y2,z2],
                         [x3,y3,z3]]
                 elements=['Ca', 'Fe', 'Sb']
                 numbers=[2, 8, 24]
                 type= Direct
                 positions=[[a1_x,a1_y,a1_z],
                           [a2_x,a2_y,a2_z],
                           [a3_x,a3_y,a3_z],
                           ...]
        """
        import re
        if self.file.endswith('.xml'):
            return parse_qe_xml(self.file)

        elif self.file.endswith('.in'):
            renat = r'nat\s*=\s*(\d+)'
            nat = 0
            with open(self.file,'r') as f:
                for line in f:
                    if 'nat' in line and re.findall(renat,line):
                       nat = int(re.findall(renat,line)[0])
                       print(nat)

                    if 'CELL_PARAMETERS' in line:
                        cellunit = line.split()[1]
                        lattice = []
                        for i in range(3):
                            lat = f.readline().split()
                            assert len(lat) == 3
                            lattice.append(lat)

                    elif 'ATOMIC_POSITIONS' in line:
                        posunit = line.split()[1]
                        elmdict = {}
                        for i in range(nat):
                            apos = f.readline().split()
                            elm = apos[0]
                            if elm not in elmdict:
                                elmdict[elm] = []
                            elmdict[elm].append(apos[1:4])
                        
            # data process %
            if cellunit == 'angstrom':
                lattice = np.array(lattice,dtype=float)  
            elif cellunit == 'bohr':
                lattice = np.array(lattice,dtype=float) * 0.529177  
            else:
                raise KeyError("Unsupport CELL_PARAMETER Unit. ")

            elements = []
            numbers = []
            positions = []
            for elm,position in elmdict.items():
                elements.append(elm)
                numbers.append(len(position))
                positions.extend(position)
            positions = np.array(positions,dtype=float)
            
            if posunit == 'angstrom':
                type = 'Cartesian'
            elif posunit == 'bohr':
                type = 'Cartesian'
                positions = positions*0.529177
            elif posunit == 'crystal':
                type = 'Direct'
            else:
                raise KeyError("Unsupport ATOMIC_POSITIONS Unit. ")
                
        espessro = {'comment': 'jamip',
                    'lattice':lattice,
                    'elements':elements,
                    'numbers':numbers,
                    'type': type,
                    'positions':positions}
        return espessro
    
    def __readCIF(self):
        """
        read CIF file

        returns:
            cif: A dictionary including:
                 lattice=[[x1,y1,z1],
                         [x2,y2,z2],
                         [x3,y3,z3]]
                 elements=['Ca', 'Fe', 'Sb']
                 numbers=[2, 8, 24]
                 type= Direct
                 positions=[[a1_x,a1_y,a1_z],
                           [a2_x,a2_y,a2_z],
                           [a3_x,a3_y,a3_z],
                           ...]

        """
        import re
        cf=parse_cif(self.file)
        cb=cf[0][1]

        # lattice parameters
        aa=float(cb['_cell_length_a'])
        bb=float(cb['_cell_length_b'])
        cc=float(cb['_cell_length_c'])
        alpha=float(cb['_cell_angle_alpha'])
        beta=float(cb['_cell_angle_beta'])
        gamma=float(cb['_cell_angle_gamma'])
        alpha=alpha*(np.pi/180)
        beta=beta*(np.pi/180)
        gamma=gamma*(np.pi/180)

        # lattice vector
        lattice=[]
        lattice=lattice_vector(aa, bb, cc, alpha, beta, gamma)

        # elements
        elements=[]
        for symbol in cb['_atom_site_type_symbol']:
            e = re.findall("[A-Z][a-z]?",symbol)
            if len(e) == 1:
                elements.append(e[0])
            else:
                raise ValueError("Unknown element symbol %s" %symbol)
        
        # space group number
        if '_space_group.it_number' in cb:
            group_number=str(cb['_space_group.it_number'])
        elif '_space_group_it_number' in cb:
            group_number=str(cb['_space_group_it_number'])
        elif '_symmetry_int_tables_number' in cb:
            group_number=str(cb['_symmetry_int_tables_number'])
        else:
            group_number=None

        # space group H-M symbol
        if '_space_group.Patterson_name_h-m' in cb:
            symbolHM=format_symbol(cb['_space_group.patterson_name_h-m'])
        elif '_symmetry_space_group_name_h-m' in cb:
            symbolHM=format_symbol(cb['_symmetry_space_group_name_h-m'])
        else:
            symbolHM=None


        # symmetry operations
        for name in ['_space_group_symop_operation_xyz',
                     '_space_group_symop.operation_xyz',
                     '_symmetry_equiv_pos_as_xyz']:
            if name in cb:
                sitesym=cb[name]
                break
        else:
            sitesym=None

        # positions
        positions=[]
        if sitesym:
            positions=equival_pos(sitesym, cb)
        elif symbolHM:
            if SG.get(symbolHM):
                sitesym = SG.get(symbolHM)
                positions=equival_pos(SG.get(symbolHM), cb)
            else:
                raise SpacegroupNotFoundError('invalid spacegroup %s, not found in data base' %
                                              (symbolHM,))
        elif group_number:
            sitesym = SG.get(group_number)
            positions=equival_pos(SG.get(group_number), cb)
        else:
            raise SpacegroupValueError('either *number* or *symbol* must be given for space group!')
   
        # numbers
        numbers=[]
        if '_atom_site_symmetry_multiplicity' in cb:
            numbers=cb['_atom_site_symmetry_multiplicity']
        elif sitesym:
            numbers=numbers_cal(sitesym, cb)

        # compare numbers and positions.
        if len(positions) > sum(numbers):
            import warnings
            CIFError = "Total number of atom_coords beyond the CIF declaration in %s with accuracy of 1E-3 ! Reset the accuracy to 1E-2." %self.file
            warnings.warn(CIFError) 
            positions=equival_pos(sitesym, cb, prec=1e-2)

        assert len(positions) == sum(numbers)

        # comment
        for name in ['_chemical_formula_structural',
                     '_chemical_formula_sum']:
            if name in cb:
                comment = cb[name]
                break
        else:
            comment = None

        # join elements
        if len(elements) != len(set(elements)):
            edict = {}
            index = 0
            for elm,num in zip(elements,numbers):
                if elm not in edict:
                    edict[elm] = list(range(index,index+num)) 
                else:
                    edict[elm].extend(list(range(index,index+num)))
                index += num

            elements=[]
            numbers = []
            new_positions = []
            for elm in edict:
                index = np.array(edict[elm])
                elements.append(elm)
                numbers.append(len(index))
                for i in index:
                    new_positions.append(positions[i])
            positions = new_positions

        # type
        type='Direct'

        lattice=np.array(lattice)
        elements=np.array(elements)
        numbers=np.array(numbers)
        positions=np.array(positions)
        

        cif={'comment':comment,
             'lattice': lattice,
             
             'elements': elements,
             'numbers': numbers,
             'type': type,
             'positions': positions}

        return cif       
    
    def __readPOSCAR(self): # only for VASP5.x (It means the file need to contain the element information)
        """
        read POSCAR file
        
        poscar:
            comment: comment of the first line
            lattice=[[x1,y1,z1],
                     [x2,y2,z2],
                     [x3,y3,z3]]
            elements=['Ca', 'Fe', 'Sb']
            numbers=[2, 8, 24]
            type= Direct or Cartesian
            positions=[[a1_x,a1_y,a1_z],
                      [a2_x,a2_y,a2_z],
                      [a3_x,a3_y,a3_z],
                      ...]
            constraints=[[T,T,T], # Selective dynamics (optional)
                        [F,F,F],
                        [T,F,T],
                        ...]
        
        returns:
            json's object of a structure
            
        """
        input=open(self.file)
        
        # comment
        comment=''
        string=input.readline()
        if string != "":
            #comment=string.split('\n')[0]
            comment = string.strip()
            
        scale=float(input.readline())
        
        # lattice
        # ensure all structure's scale equal 1 inside the program     
        lattice=[]
        for i in range(0,3):
            try:
                tmp=np.array(input.readline().split(),dtype=float)
                assert tmp.shape[0] == 3
                lattice.append(tmp*scale)
            except ValueError:
                print("can't transfer literal to float type!")
                exit()
        lattice=np.array(lattice)
        
        # element VASP5.x
        # Note that:
        #   need check symbol of element is valid by comparing the element table in jamipdb
        elements=[]
        tmp=np.array(input.readline().split())
        for i in range(0,tmp.shape[0]):
            if not(tmp[i].isalpha()):
                print('elements contain non-alphabet!')
                exit()
        elements=tmp
        
        # numbers
        numbers=[]
        try:
            tmp=np.array([int(s0) for s0 in input.readline().split()])
            if elements.shape[0] != tmp.shape[0]:
                print("length of numbers don't match with that of elements")
                exit()
            numbers=tmp
        except ValueError:
            print("can't transfer literal to int type!")
            exit()
            
        
        tmp=input.readline()
        isConstraint=False
        type=''
        if tmp.lower().startswith('s'): # Selective dynamics
            isConstraint=True
            # type
            tmp=input.readline()
            if tmp.lower().startswith('c'):
                type='Cartesian'
            elif tmp.lower().startswith('d'):
                type='Direct'
            else:
                print('type of POSCAR is invalid')
                exit()
        # type    
        elif tmp.lower().startswith('c'):
            type='Cartesian'
        elif tmp.lower().startswith('d'):
            type='Direct'
        else:
            print('type of POSCAR is invalid')
            exit()
        
        # position
        natoms=sum(numbers)
        positions=[]
        constraints=[]
        for i in range(0, natoms):
            try:
                string=input.readline().split()
                positions.append(np.array(string[:3],dtype='float'))

                # constraint
                if isConstraint :
                    assert len(string) == 6
                    tmp=np.array([False if s0.startswith('F') else True for s0 in string[3:6]])
                    constraints.append(tmp)
                    
            except ValueError:
                ("can't transfer literal to float type!")
                exit()
        positions=np.array(positions)
        if type == 'Cartesian':
            positions = positions*scale
        constraints=np.array((constraints))

        # velocity
        velocities = []
        for line in input:
            if line.strip():
                v = line.split()
                if len(v) != 3: break
                velocities.append(v)
        if len(velocities) == natoms:
            velocities = np.array(velocities, dtype=float)
        else: 
            velocities = []
        
        input.close()
        poscar={'comment':comment,
                'lattice':lattice,
                'elements':elements,
                'numbers':numbers,
                'type':type,
                'positions':positions,
                'velocities':velocities,
                'constraints':constraints}
        return poscar

    def __readXYZ(self):
        """
        read xyz file
            
        poscar:
            elements=['Ca', 'Fe', 'Sb']
            numbers=[2, 8, 24]
            positions=[[a1_x,a1_y,a1_z],
                      [a2_x,a2_y,a2_z],
                      [a3_x,a3_y,a3_z],
                      ...]
        Note: coordinate type of positions can only be Cartesian.
        
        returns:
            object of a structure
        """
        xyz=()
        input=open(self.file)
        
        # natoms
        try:
            natoms=int(input.readline())
        except ValueError:
            return ValueError('invalid natoms in xyz file!')
        
        # comment
        comment=input.readline() # skip
        
        # atoms
        counter=0 # counter of atoms
        atoms={}
        string=input.readline()
        while(string):
            if string.split() != []: # skip blank line
                ntmp=string.split()[0] # atomic name
                try:
                    ptmp=np.array([float(s0) for s0 in string.split()[1:]]) # atomic position
                except ValueError:
                    raise ValueError('invalid atomic position in xyz file!')
                
                if ntmp in atoms.keys():
                    value=atoms[ntmp]
                    atoms[ntmp]=np.vstack((value,ptmp))
                else:
                    atoms[ntmp]=ptmp
                counter=counter+1
                string=input.readline()
                
        if counter != natoms:
            raise ReadError("number of atoms doesn't match!")
        
        # conversion format
        molecule={}
        molecule['elements']=np.array(atoms.keys())
        numbers=[]
        positions=[]
        for e in atoms.keys():
            dim=atoms[e].shape
            if len(dim) == 1 and dim[0] == 3:
                numbers.append(1)
                positions.append(atoms[e])
            elif len(dim) == 2 and dim[1] == 3:
                numbers.append(dim[0])
                for p in range(0,dim[0]):
                    positions.append(atoms[e][p])
            else:
                raise ReadError('invalid atomic position!')
            
        molecule['numbers']=np.array(numbers)
        molecule['positions']=np.array(positions)
        
        return molecule
                
    def __readMOL(self):
        """
        """
        pass
# coding: utf-8
# Copyright (c) JUMP2 Development Team.
# Distributed under the terms of the JLU License.


#=================================================================
# This file is part of JUMP2.
#
# Copyright (C) 2017 Jilin University
#
#  Jump2 is a platform for high throughput calculation. It aims to 
#  make simple to organize and run large numbers of tasks on the 
#  superclusters and post-process the calculated results.
#  
#  Jump2 is a useful packages integrated the interfaces for ab initio 
#  programs, such as, VASP, Guassian, QE, Abinit and 
#  comprehensive workflows for automatically calculating by using 
#  simple parameters. Lots of methods to organize the structures 
#  for high throughput calculation are provided, such as alloy,
#  heterostructures, etc.The large number of data are appended in
#  the MySQL databases for further analysis by using machine 
#  learning.
#
#  Jump2 is free software. You can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published 
#  by the Free sofware Foundation, either version 3 of the License,
#  or (at your option) and later version.
# 
#  You should have recieved a copy of the GNU General Pulbic Lincense
#  along with Jump2. If not, see <https://www.gnu.org/licenses/>.
#=================================================================

"""
Module to read cif file and return a dictionary of POSCAR.

    poscar={'lattice':lattice,
            'elements':elements,
            'numbers':numbers,
            'type':type,
            'positions':positions,
           }

"""

#from spaceGroupD3 import spacegroups as SG

class SpacegroupError(Exception):
    """Base exception for the spacegroup module."""
    pass

class SpacegroupNotFoundError(SpacegroupError):
    """Raised when given space group cannot be found in data base."""
    pass

class SpacegroupValueError(SpacegroupError):
    """Raised when arguments have invalid value."""
    pass

def convert_value(value):
    """
    Convert CIF value string to corresponding python type.

    Arguments:
        value: A number string which needs to be translated to float value.

    Returns:
        value: Object of a float value.

    """
    import re
    import warnings
    value=value.strip()
    if re.match('(".*")|(\'.*\')$', value):
        return value[1:-1]
    elif re.match(r'[+-]?\d+$', value):
        return int(value)
    elif re.match(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$', value):
        return float(value)
    elif re.match(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\(\d+\)$',
                  value):
        return float(value[:value.index('(')])  # strip off uncertainties
    elif re.match(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\(\d+$',
                  value):
        warnings.warn('Badly formed number: "{0}"'.format(value))
        return float(value[:value.index('(')])  # strip off uncertainties
    else:
        return value


def parse_multiline_string(lines, line):
    """
    Parse semicolon-enclosed multiline string and return it.

    """
    assert line[0] == ';'
    strings = [line[1:].lstrip()]
    while True:
        line = lines.pop().strip()
        if line[:1] == ';':
            break
        strings.append(line)
    return '\n'.join(strings).strip()


def parse_singletag(lines, line):
    """
    Parse a CIF tag(entries starting with underscore). Returns
    a key-value pair.

    Arguments:
        lines: All lines.
        line: A single line starts with '_'.

    Return:
        key: The single tag(entries starting with underscore) as key.
        convert_value(value): The single value corresponded to the tag.

    Examples:
        The string '_symmetry_Int_Tables_number       62' will
        be translated to a key-value pair: {'_symmetry_Int_Tables_number': 62}.

    """
    kv = line.split(None, 1)
    if len(kv) == 1:
        key = line
        line = lines.pop().strip()
        while not line or line[0] == '#':
            line = lines.pop().strip()
        if line[0] == ';':
            value=parse_multiline_string(lines, line)
        else:
            value=line
    else:
        key, value=kv
    return key, convert_value(value)


def parse_loop(lines):
    """
    Parse a CIF loop. Returns a dict with column tag names as keys
    and a lists of the column content as values.

    Arguments:
        lines: The all lines in cif file.

    Return:
        column: A column based dictionary about the tags and
        corresponding values in a loop.

    """
    import shlex
    import warnings
    header = []
    line = lines.pop().strip()
    while line.startswith('_'):
        header.append(line.lower())
        line = lines.pop().strip()
    columns = dict([(h, []) for h in header])

    tokens = []
    while True:
        lowerline = line.lower()
        if (not line or
            line.startswith('_') or
            lowerline.startswith('data_') or
            lowerline.startswith('loop_')):
            break
        if line.startswith('#'):
            line = lines.pop().strip()
            continue
        if line.startswith(';'):
            t = [parse_multiline_string(lines, line)]
        else:
            if len(header) == 1:
                t = [line]
            else:
                t = shlex.split(line, posix=False)

        line = lines.pop().strip()

        tokens.extend(t)
        if len(tokens) < len(columns):
            continue
        if len(tokens) == len(header):
            for h, t in zip(header, tokens):
                columns[h].append(convert_value(t))
        else:
            warnings.warn('Wrong number of tokens: {0}'.format(tokens))
        tokens = []
    if line:
        lines.append(line)
    return columns


def parse_items(lines, line):
    """
    Parse a CIF data items and return a dict with all tags.

    Arguments:
        lines: The all lines in cif file.
        line: A single line which will be translated to a key-value pair
        or just be a single tag.

    Return:
        tags: The all key-value pairs obtained from parse_singletag
        and parse_loop.

    """
    tags = {}
    while True:
        if not lines:
            break
        line = lines.pop()
        if not line:
            break
        line = line.strip()
        lowerline = line.lower()
        if not line or line.startswith('#'):
            continue
        elif line.startswith('_'):
            key, value = parse_singletag(lines, line)
            tags[key.lower()] = value
        elif lowerline.startswith('loop_'):
            tags.update(parse_loop(lines))
        elif lowerline.startswith('data_'):
            if line:
                lines.append(line)
            break
        elif line.startswith(';'):
            parse_multiline_string(lines, line)
        else:
            raise ValueError('Unexpected CIF file entry: "{0}"'.format(line))
    return tags


def parse_block(lines, line):
    """
    Parse a CIF data block and return a tuple with the block name
    and a dict with all tags.

    Arguments:
        lines: The all lines in cif file.
        line: A single line which will be a single tag.

    Return:
        blockname: The name of a block which starts with 'data_'.
        tags: The all tags.

    """
    assert line.lower().startswith('data_')
    blockname = line.split('_', 1)[1].rstrip()
    tags = parse_items(lines, line)
    return blockname, tags


def parse_cif(fileobj):
    """
    Parse a CIF file. Returns a list of blockname and tag pairs.
    All tag names are converted to lower case.

    Arguments:
        fileobj: The cif file name.

    Return:
        blocks:The all blocks obtained from parse_block. (The number
        of the blocks is usually 2)

    """
    if isinstance(fileobj, str):
        fileobj = open(fileobj)
    lines = [''] + fileobj.readlines()[::-1]  # all lines (reversed)
    blocks = []
    while True:
        if not lines:
            break
        line = lines.pop()
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        blocks.append(parse_block(lines, line))
    return blocks

def format_symbol(symbol):
    """
    Returns well formatted Hermann-Mauguin symbol as extected by
    the database, by correcting the case and adding missing or
    removing duplicated spaces.

    """
    fixed = []
    s = symbol.strip()
    s = s[0].upper() + s[1:].lower()
    for c in s:
        if c.isalpha():
            if len(fixed) and fixed[-1] == '/':
                fixed.append(c)
            else:
                fixed.append(' ' + c + ' ')
        elif c.isspace():
            fixed.append(' ')
        elif c.isdigit():
            fixed.append(c)
        elif c == '-':
            fixed.append(' ' + c)
        elif c == '/':
            fixed.append(c)
    s = ''.join(fixed).strip()
    return ' '.join(s.split())

def equival_pos(equival, ci, prec=1e-3):
    """
    Translate the initial position coordinates to
    symmetry equivalent position coordinates.

    Arguments:
        equival: The tag (no, symbolHM or  sitesym)corresponding to
        symmetry operations.
        ci: The cif file resource.
        sum_pos: The total number of atoms in crystal. 

    Return:
        symXYZ: A list contains the equivalent position coordinates.

    """
    import re

    allXYZ = []
    symXYZ = []
    for X, Y, Z in zip(ci['_atom_site_fract_x'],
                       ci['_atom_site_fract_y'],
                       ci['_atom_site_fract_z']):
        atommap = {'x':float(X),'y':float(Y),'z':float(Z)}

        for operation in equival:
            temp = operation.split(',')
            atomL = []
            for strs in temp:
                value = eval(strs,atommap)
                fraction = re.findall(r'\d+\.?\d?/\d+\.?\d?',strs)
                if len(fraction) > 0:
                    denominator = float(fraction[0].split('/')[1])
                    norm = np.around(value*denominator)
                    if np.abs(norm-value*denominator) < prec:
                        value = norm/denominator
                elif np.abs(np.around(value)-value) < prec:
                    value = np.around(value)
                atomL.append(value)
            atomL = np.array(atomL) - np.floor(atomL)
            allXYZ.append(atomL)

    for i in allXYZ:
        if len(symXYZ) == 0:
            symXYZ = i[np.newaxis, :]
        elif np.min(np.abs(symXYZ-i).sum(axis=1)) > 3*prec:
            symXYZ = np.vstack((symXYZ,i))

    return symXYZ

def numbers_cal(equival, ci):
    """
    Calculate the number of atoms of each type.

    Arguments:
        equival: The tag (no, symbolHM or  sitesym)corresponding to
        symmetry operations.
        ci: The cif file resource.

    Return:
        numbers: The number of atoms of each type.

    """
    numXYZ = []
    atomN = []
    numbers = []

    for X, Y, Z in zip(ci['_atom_site_fract_x'],
                       ci['_atom_site_fract_y'],
                       ci['_atom_site_fract_z']):
        atomX = float(X)
        atomY = float(Y)
        atomZ = float(Z)

        for operation in equival:
            temp = operation.split(',')

            XX = temp[0].replace('1/2', '1./2.').replace('1/4', '1./4.')
            XX = XX.replace('3/4', '3./4.').replace('1/', '1./6.')
            XX = XX.replace('1/3', '1./3.').replace('2/3', '2./3.')
            XXX = XX.replace('5/6', '5./6.')

            YY = temp[1].replace('1/2', '1./2.').replace('1/4', '1./4.')
            YY = YY.replace('3/4', '3./4.').replace('1/6', '1./6.')
            YY = YY.replace('1/3', '1./3.').replace('2/3', '2./3.')
            YYY = YY.replace('5/6', '5./6.')

            ZZ = temp[2].replace('1/2', '1./2.').replace('1/4', '1./4.')
            ZZ = ZZ.replace('3/4', '3./4.').replace('1/6', '1./6.')
            ZZ = ZZ.replace('1/3', '1./3.').replace('2/3', '2./3.')
            ZZZ = ZZ.replace('5/6', '5./6.')

            x = atomX
            y = atomY
            z = atomZ

            XXXX = eval(XXX)
            YYYY = eval(YYY)
            ZZZZ = eval(ZZZ)

            if XXXX < 0:
                XXXX = 1.0 + XXXX

            if YYYY < 0:
                YYYY = 1.0 + YYYY

            if ZZZZ < 0:
                ZZZZ = 1.0 + ZZZZ

            if XXXX >= 1.0:
                XXXX = XXXX - 1.0

            if YYYY >= 1.0:
                YYYY = YYYY - 1.0

            if ZZZZ >= 1.0:
                ZZZZ = ZZZZ - 1.0

            atomL = [XXXX, YYYY, ZZZZ]
            numXYZ.append(atomL)

        # calculate the number of atoms of each type.
        for i in numXYZ:
            if not i in atomN:
                atomN.append(i)
        temp = len(atomN)
        numbers.append(temp)
        numXYZ = []
        atomN = []

    return numbers

def lattice_vector(a, b, c, alpha, beta, gamma):
    """
    Translate lattice parameters to lattice vector.

    Arguments:
        a: The module of lattice parameter a.
        b: The module of lattice parameter b.
        c: The module of lattice parameter c.
        alpha: The included angle between vector b and c.
        beta: The included angle between vector a and c.
        gamma: The included angle between vector a and b.

    Return:
        latticeV: A list about lattice vector expressed by direct coordinate.

    """

    ax = a
    ay = 0.
    az = 0.
    bx = b * np.cos(gamma)
    by = b * np.sin(gamma)
    bz = 0.
    cx = c * np.cos(beta)
    cy = c * ((np.cos(alpha) - np.cos(beta) * np.cos(gamma)) / np.sin(gamma))
    cz = c * (np.power(1 + 2 * np.cos(alpha) * np.cos(beta) * np.cos(gamma)
                        - np.power(np.cos(alpha), 2) - np.power(np.cos(beta), 2)
                        - np.power(np.cos(gamma), 2), 0.5) / np.sin(gamma))
    latticeV = [[ax, ay, az],
                [bx, by, bz],
                [cx, cy, cz]]

    return latticeV

def parse_qe_xml(xmlfile):
    ''' 
        input:
            qe: A xml including:
            atomic_postions: atom name, [x1,x2,x3], ...
            type= Direct
            cell: [[x1,y1,z1],
                   [x2,y2,y3],
                   [x3,y3,z3]] # unit: bohr
            1 bohr = 0.529177 ang 
    ''' 
    import xml.etree.cElementTree as ET

    for event, elem in ET.iterparse(xmlfile,events=('start', 'end')):
        if event =='start':
            if elem.tag == 'output':
                atoms = elem.findall('./atomic_structure/atomic_positions/atom')
                posdict = {}
                for atom in atoms:
                    element = atom.get('name')
                    if element not in posdict:
                        posdict[element] = []                
                    posdict[element].append(atom.text.split())
                cell = elem.find('./atomic_structure/cell')
                lattice = []
                for child in cell:
                    lattice.append(np.array(child.text.split(),dtype=float))
                break
        elem.clear()

    # returns %
    elements = []
    numbers = []
    positions = []
    for elm,position in posdict.items():
        elements.append(elm)
        numbers.append(len(position))
        positions.extend(position)
    lattice = np.asarray(lattice)*0.529177
    positions = np.array(positions,dtype=float)*0.529177

    espessro = {'comment': 'jamip',
                'lattice':lattice,
                'elements':elements,
                'numbers':numbers,
                'type': 'Cartesian',
                'positions':positions}
    return espessro

