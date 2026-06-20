import os
import re
import numpy as np
from os.path import exists,join
from typing import Union
from jamip.analysis.vasp.outcar import GrepOutcar
from jamip.analysis.qe.qexml import GrepXml

class Finder:

    __task__ = None
    __builder__ = None
    __multi__ = False
    _stdin = None

    def __init__(self,stdin=None):
        self.stdin = stdin

    def grep(self,value):
        if self.__builder__ == 'vasp':
            func = getattr(GrepOutcar(),value)
        elif self.__builder__ == 'qe':
            func = getattr(GrepXml(),value)
        elif self.__builder__ == 'jamip':
            func = getattr(GrepOutcar(),value)
        elif self.__builder__ == None:
            raise ValueError('Use the grep module before setting up the software.')
        return func(self.stdscf)

    @property
    def task(self):
        return self.__task__
        
    @property
    def stdin(self):
        return self._stdin

    @property
    def stdin(self,path):
        path = self.seek(path)
        if path != None:
            self._stdin = path
        else:
            raise IOError("Missing calculation files!")

    @property
    def stdscf(self):

        if self.__builder__ == 'jamip':
            if exists(join(self._stdin, 'scf', 'OUTCAR')):
                return join(self._stdin, 'scf')
            elif exists(join(self._stdin, 'qerun', 'scf.xml')):
                return join(self._stdin, 'qerun', 'scf.xml')
        elif self.__multi__ == False:
            return self._stdin
        else:
            raise IOError('Seek scf directoty failed!')

    @property
    def stdcell(self):

        if self.__builder__ == 'jamip':
            contcar = join(self._stdin, 'scf', 'CONTCAR')
            poscar = join(self._stdin, 'scf', 'POSCAR')
        elif self.__multi__ == False:
            contcar = join(self._stdin, 'CONTCAR')
            poscar = join(self._stdin, 'POSCAR')
        else:
            raise IOError('Seek scf directoty failed!')

        if exists(contcar):
            return contcar
        elif exists(poscar):
            return poscar
        else:
            raise OSError('Seek std_structure failed!')

    def seek(self,path):
        '''
        get calculation type, return absolute path if exists
        '''
        from os.path import normcase, isdir, isfile

        path = normcase(path)
        if isdir(path):
            if exists(join(path,'.status')):
                self.__builder__ = 'jamip'
            elif exists(join(path,'OUTCAR')):
                self.__builder__ = 'vasp'
            else:
                path = None

        elif isfile(path) and path.endswith('.xml'):
            self.__builder__ = 'qe'

        else:
            path = None

        return path

class FinderSet:

    __builder__ = None
    _stdin = None

 
    def __init__(self,inputs):
        self.stdin = inputs
        self.syspath = set()
        self.sysfile = set()

    @property
    def stdin(self):

        return self.syspath,self.sysfile

    @stdin.setter
    def stdin(self,value:Union[str,list]):

        from os.path import isfile,isdir,abspath

        if isinstance(value,str): value = [value]
        for path in value:
            if isfile(path):
                self.sysfile.add(abspath(path))
            elif isdir(path):
                self.sysfile.add(abspath(path))

    def seek_ftype(self, filename):

        from os.path import abspath,isfile

        ftype = None
        if isfile(filename):
            if filename.endswith('.cif'):
                ftype='cif'
            elif filename.endswith('.xyz'):
                ftype='xyz'
            elif filename.endswith('.mol'):
                ftype='mol'
            elif filename.endswith('.vasp'):
                ftype = 'poscar'
            elif 'CONTCAR' in os.path.basename(filename):
                ftype='poscar'
            elif 'POSCAR' in os.path.basename(filename):
                ftype='poscar'

        return ftype
       

    def seek_entry(self, path):

        from os.path import isdir, isfile, abspath

        root = abspath(path)
        entrys = []
        if not isdir(path):
            raise ValueError('The input path is not a directory!')

        if isfile(join(root,'.status')) or isfile(join(root,'OUTCAR')):
            entry.append(root)
        else:
            for dir in os.listdir(root):
                if isfile(join(root,dir,'.status')) or isfile(join(root,dir,'POSCAR')):
                    entry.append(join(root,dir))

        return entry

    @property
    def entrys(self):
        import pickle       

        _entrys = []
        for dir in self.syspath:
            _entrys.extend(self.seek_entry(dir))

        for file in self.sysfile:
            if file.endswith('.dat') or file.endswith('.pool'):
                try:
                    root = abspath(dirname(file))
                    with open(file,'rb') as f:
                        pool=pickle.load(f)
                    for dir in pool.keys():
                        if isfile(join(root,dir,'.status')):
                            _entrys.append(join(root,dir))
                except:
                    pass

        return list(set(_entrys))

    @property
    def structures(self):
        
        from os.path import join
        from jamip.structure import read

        _structures = []
        for dir in self.syspath:
            for filename in os.listdir(root):
                path = join(root,filename)
                if self.seek_ftype(path):
                    _structures.append(path)
        for file in self.sysfile:
            if self.seek_ftype(file):
                _structures.append(file)

        return list(set(_structures))
