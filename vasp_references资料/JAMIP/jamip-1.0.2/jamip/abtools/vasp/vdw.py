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

#from ...error import *

#from periodictable import elements

__contributor__ = 'Gaungren Na, Xingang Zhao'
__update_date__ = '2017.05.01'

"""SetVdw:: partial of JUMP2 for vdw functional setting, default is None."""


class VDW(object):
    """
    Common Van der Waals functional implemented in VASP:
        --D2: 
        --optB86b:
        --optB88:
        --DF2:
        --optPBE:
        --revPBE:
        --revDF2:
        --rVV10:
    args::
        vdw:: a string to describe the vdw functional name;
        elements:: species only for D2 functional;

    :return: A parameter dict.
    """
     
    def __init__(self):
	
        self.__vdw = None

    @property
    def vdw(self):

        return self.__vdw

    @vdw.setter
    def vdw(self, value=None):
        
        if isinstance(value, str):
            vdw = value.lower()
            if vdw.startswith('d2'):
                self.__vdw = 'D2'
            elif vdw.startswith('b86'):
                self.__vdw = 'B86'
            elif vdw.startswith('b88'):
                self.__vdw = 'B88'
            elif vdw.startswith('pbe'):
                self.__vdw = 'PBE'
            elif vdw.startswith('df2'):
                self.__vdw = 'DF2'
            elif vdw.startswith('revdf2'):
                self.__vdw = 'rDF2'
            elif vdw.startswith('rvv10'):
                self.__vdw = 'rVV10'
            elif vdw.startswith('revpbe'):
                self.__vdw = 'rPBE'
            elif vdw.startswith('optpbe'):
                self.__vdw = 'oPBE'
            else:
                raise IOError ('No such vdw functional !')

    @vdw.deleter
    def vdw(self):
         
        del self.__vdw

    @property
    def vdw_tasks(self):
 
        return self._vdw_tasks if hasattr(self,'_vdw_tasks') else ['relax','accelerate']
 
    @vdw_tasks.setter
    def vdw_tasks(self, value:str):

        self._vdw_tasks = value.split()

    def __d2vdw__(self, species):

        c6 = [ 0.14 ,  0.08 ,  1.61 ,  1.61 ,  3.13 ,  1.75 ,  1.23 ,  0.7  ,
         0.75 ,  0.63 ,  5.71 ,  5.71 , 10.79 ,  9.23 ,  7.84 ,  5.57 ,
         5.07 ,  4.61 , 10.8  , 10.8  , 10.8  , 10.8  , 10.8  , 10.8  ,
        10.8  , 10.8  , 10.8  , 10.8  , 10.8  , 10.8  , 16.99 , 17.1  ,
        16.37 , 12.64 , 12.47 , 12.01 , 24.67 , 24.67 , 24.67 , 24.67 ,
        24.67 , 24.67 , 24.67 , 24.67 , 24.67 , 24.67 , 24.67 , 24.67 ,
        37.32 , 38.71 , 38.44 , 31.74 , 31.5  , 29.99 ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ]

        r0 = [ 1.001,  1.012,  0.825,  1.408,  1.485,  1.452,  1.397,  1.342,
         1.287,  1.243,  1.144,  1.364,  1.716,  1.716,  1.705,  1.683,
         1.639,  1.595,  1.485,  1.474,  1.562,  1.562,  1.562,  1.562,
         1.562,  1.562,  1.562,  1.562,  1.562,  1.562,  1.65 ,  1.727,
         1.76 ,  1.771,  1.749,  1.727,  1.628,  1.606,  1.639,  1.639,
         1.639,  1.639,  1.639,  1.639,  1.639,  1.639,  1.639,  1.639,
         1.672,  1.804,  1.881,  1.892,  1.892,  1.881,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ,
         0.   ,  0.   ,  0.   ,  0.   ,  0.   ,  0.   ]

        R0 = []
        C6 = []
	
        # need to updated % D2 not enough %

        for i, elm in enumerate(species):
            id = elements.symbol(elm).number
            if id > 55: print('Warning: no R0 and C6 values for '+ elm)
		    
            R0.append(r0[id])
            C6.append(c6[id])

        return  {\
            "lvdw": True, \
            "vdw_r0": ' '.join(str(r) for r in R0), \
            "vdw_c6": ' '.join(str(c) for c in C6)}
            

    def vdw_parameters(self, elements=None):

        value = self.vdw

        # case d2 vdw %
        if value == 'D2':
            return self.__d2vdw__(elements)

        # case optPBE vdw % 
        if value == 'oPBE':
            return {\
                'gga': 'OR', \
                'luse_vdw': True, \
                "lasph":True, \
                'aggac': 0.0000}
                

        # for optvdw-B88 %
        if value == 'B88':
            return {\
                'gga': 'BO', \
                'luse_vdw': True, \
                "lasph":True, \
                'aggac': 0.0000, \
                'param1': 0.1833333333, \
                'param2': 0.2200000000}
                

        # for optvdw-B86b %
        if value == 'B86':
            return {\
                'gga': 'MK', \
                'luse_vdw': True, \
                "lasph":True, \
                'param1': 0.1234, \
                'param2': 1.0000, \
                'aggac': 0.0000}
                

        # for DF2 %
        if value == 'DF2':
            return {\
                "gga": 'ML', \
                "luse_vdw": True, \
                "aggac": 0.0000, \
                "lasph":True, \
                "zab_vdw": -1.8867}
                
        # for revDF2 %
        if value == 'rDF2':
            return {\
                "gga": 'ML', \
                "luse_vdw": True, \
                "aggac": 0.0000, \
                "lasph":True, \
                'param1': 0.1234, \
                'param2': 0.711357, \
                "zab_vdw": -1.8867}
                
        # for revPBE %
        if value == 'rPBE':
            return {\
                "gga": 'Re', \
                "luse_vdw": True, \
                "aggac": 0.0000, \
                "lasph": True}
                
        # for scan+rvv10 %
        if value == 'rVV10':
            return {\
                "gga": 'SCAN', \
                "luse_vdw": True, \
                "bparam": 15.7, \
                "lasph": True}
                
