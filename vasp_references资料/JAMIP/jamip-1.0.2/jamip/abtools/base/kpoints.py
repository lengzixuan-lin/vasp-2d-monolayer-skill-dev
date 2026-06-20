import numpy as np
from dataclasses import dataclass
from typing import List,Union
from collections import Iterable

class Kpath:
   

    def __init__(self, *args, **kwargs):
        pass

    def __setattr__(self, key, item):
        if isinstance(item, int):
            self.__dict__[key] = item
        else:
            self.__dict__[key] = Kpoints()
            self.__dict__[key].kpoints = item

    def __contains__(self, key):
        return key in self.__dict__

    def __setitem__(self, key, item): 
        self.__dict__[key] = item

    def __getitem__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        raise KeyError(key)

    def __deepcopy__(self,memo):
        from copy import deepcopy
        cp = Kpath()
        for key, value in self.__dict__.items():
            cp[key] = deepcopy(value)
        return cp

@dataclass
class __KPT__:
    ''' class of Kpoints rec posiation '''
    name: str
    position: np.ndarray

    def __repr__(self):
        return '\n{0[0]:14.8f}{0[1]:14.8f}{0[2]:14.8f} ! {1}'.format(self.position,self.name)

    def __str__(self):
        return '{0[0]:.4f} {0[1]:.4f} {0[2]:.4f} ! {1}'.format(self.position,self.name)

class __KPATH__:
    ''' class of hym Kpath '''
    
    def __init__(self, kpath, insert: Union[int,List[int]]=30):

        if isinstance(kpath[0], __KPT__):
            self.kpath = kpath
            if isinstance(insert, list):
                assert len(kpath) == len(insert)
            self.num = len(kpath)
            self.insert = insert

        elif isinstance(kpath[0][0], __KPT__):

            kpts = []
            ints = []
            num = 0

            for ks in kpath:
                for i,k in enumerate(ks):
                    kpts.append(k)
                    if i+1 < len(ks):
                        if isinstance(insert, list):
                            ints.append(insert[num])
                        else:
                            ints.append(insert)
                        num += 1
                    else:
                        ints.append(1)

            if isinstance(insert, list):
                assert len(insert) == num

            self.num = num
            self.kpath = kpts
            self.insert = ints

    def __repr__(self):
        result = ''

        if isinstance(self.insert, int):
            for i in range(1,len(self.kpath)):
                result += repr(self.kpath[i-1])
                result += repr(self.kpath[i])
                result += '\n'

        elif isinstance(self.insert, list):
            for i,v in enumerate(self.insert):
                if v > 1: 
                    result += repr(self.kpath[i])
                    result += repr(self.kpath[i+1])
                    result += '\n'

        return result

    def __str__(self):
        return 'KPATH(kpath=\n{0}, insert={1})'.format('\n'.join('%s' %s for s in self.kpath),self.insert)

    @property
    def qeformat(self):
        result = ''

        if isinstance(self.insert, int):
            insert = [self.insert]*(self.num-1) + [1]
        else:
            insert = self.insert

        for kpt, num in zip(self.kpath,insert):
            result += '{0[0]:10.6f}{0[1]:10.6f}{0[2]:10.6f}{1:4} ! {2}\n'.format(\
                      kpt.position, num, kpt.name)

        return result
 
    @classmethod
    def _from_array(cls, value, insert:int=50):
        kpath = []
        for i in value:
            kpath.append(__KPT__('K',i))
        return __KPATH__(kpath, insert)

    def split(self):

        if isinstance(self.insert, int):
            self.insert = [insert] * len(kpaths.kpath)

        keys = []
        results = []
        for i,v in enumerate(self.insert):
            if v > 1: 
                A = self.kpath[i].name.strip('\\')
                B = self.kpath[i+1].name.strip('\\')
                keys.append('{}-{}'.format(A,B))
                results.append(self.__class__([self.kpath[i], self.kpath[i+1]], v))

        return zip(keys, results)

class Kpoints(object):

    """
    Aim to produce the kmesh
    """
    
    def __init__(self, *args, **kwargs):

        self._kpoints_ = None
        self._model_ = None 
        self._kpath_ = None 
        self._comment_ = ''
        self._value_ = 0

    @property 
    def num(self):
        return self._value_ 

    @property 
    def model(self):
        return self._model_ 

    @property 
    def comment(self):
        if len(self._comment_):
            return self._comment_
        else:
            return self._model_

    @property 
    def kpath(self):
        if self._kpath_ == None:
            self._kpath_ = Kpath()
        return self._kpath_

    @property 
    def kpoints(self):
        return self._kpoints_  

    @kpoints.setter 
    def kpoints(self,value=None):

        if isinstance(value,float):         # kspacing % 
            self._model_   = 'kspacing'
            self._kpoints_ = value 

        elif isinstance(value, __KPATH__):  # line model %
            self._model_ = 'Line Model'
            self._kpoints_ = value

        elif isinstance(value,int):
            if value >= 1000:  # auto_density %
                self._model_ = 'auto_density'
                self.density = value 
                raise RuntimeError('Unrealized Function')


        elif isinstance(value,str):
            self._model_  = 'kmesh' 
            self._kpoints_ = value
            raise RuntimeError('Unrealized Function')

        elif isinstance(value,tuple):     
            insert = 30

            if len(value) == 2:
                model,kpoint = value 

            elif len(value) == 3:
                model,kpoint,insert = value 

            elif len(value) == 4:
                self._comment_,model,kpoint,insert = value

            # set kpoints base on model %
            if model.lower()[0] == 'a':  # Auto % 
                self._model_ = 'Auto'
                self._kpoints_ = int(kpoint) 

            elif model.lower()[0] in ['m', 'g']: # Gamma and Monk % 
                if model.lower()[0] == 'm':
                    self._model_ = 'Monkhorst-pack' 
                elif model.lower()[0] == 'g':
                    self._model_ = 'Gamma'

                if isinstance(kpoint,str):
                    kpoint = kpoint.split()

                if len(kpoint) == 3:
                    self._kpoints_ = np.array([kpoint, [0,0,0]],dtype=int)
                elif len(kpoint) == 6:
                    self._kpoints_ = [np.array(kpoint[:3],dtype=int),
                                      np.array(kpoint[3:],dtype=float)]
                else:
                    raise ValueError('Error Monk/Gamma type kpoint')

            elif model.lower()[0] == 'l': # Line-model % 
                self._model_ = 'Line Model'
                if isinstance(kpoint,(list,tuple)):
                    if isinstance(kpoint[0], str):
                        kpoint = [k.split() for k in kpoint]
                    num = set([len(k) for k in kpoint])
                    if len(num) == 1:
                        num = num.pop()
                    else:
                        raise ValueError('Line Model Kpoints should be same shape !')
                    
                    kpath = []
                    if num == 3:
                        for kpt in kpoint:
                            kpath.append(__KPT__('',np.array(kpt,dtype=float)))
                        self._kpoints_ = __KPATH__(kpath, insert)

                    elif num == 4:
                        for kpt in kpoint:
                            kpath.append(__KPT__(kpt[3],np.array(kpt[:3],dtype=float)))
                        self._kpoints_ = __KPATH__(kpath, insert)

                    elif num == 5:
                        insert = []
                        for kpt in kpoint:
                            kpath.append(__KPT__(kpt[3],np.array(kpt[:3],dtype=float)))
                            insert.append(int(kpt[4]))
                        self._kpoints_ = __KPATH__(kpath, insert)
                        
            elif model.lower()[0] == 'r': # Line-model % 
                self._model_ = 'Reciprocal'
                # "{0[0]:20.14f}{0[1]:20.14f}{0[2]:20.14f}{0[3]:14}\n".format(k)
                if isinstance(kpoint,Iterable):
                    if isinstance(kpoint[0], str):
                        kpoint = [k.split() for k in kpoint]
                    kpoint = np.array(kpoint,dtype=float)
                    self._value_ = len(kpoint)
 
                    assert len(kpoint.shape) == 2 
                    if kpoint.shape[1] == 3:
                        self._kpoints_ = np.column_stack((kpoint,np.ones(len(kpoint))))
                    elif kpoint.shape[1] == 4:
                        self._kpoints_ = kpoint
                    else:
                        raise ValueError('Reciprocal Model Kpoints should n*3 or n*4 list !')
                     

            elif model.lower()[0] == 'c': # Cartesian % 
                self._model_ = 'Cartesian'
                raise OSError('Unrealized Function')

            else:
                raise OSError('Unrealized Function')

    def tolist(self):
        if self.model != 'Line Model':
            raise KeyError('Unrealized Function') 
           
        kpath = []
        if isinstance(self.kpath[0], __KPT__):
            kpath.append([k.name for k in self.kpath])
        else:
            for i in self.kpath:
                kpath.append([k.name for k in self.kpath])

        return kpath
