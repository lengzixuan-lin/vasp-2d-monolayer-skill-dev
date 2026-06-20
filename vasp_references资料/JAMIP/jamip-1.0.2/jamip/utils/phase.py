import os
import re
import numpy as np
import pandas as pd
from typing import Optional, Union
import numpy.linalg as nlg
from dataclasses import dataclass

@dataclass
class dpath:
      
    ''' decomposition path  '''

    output: list
    coeff: list
    energy: int

    def __eq__(self, other):
       
        if isinstance(other, self.__class__):
            if np.max(self.coeff - other.coeff) < 1e-4:
                return True
        return False


class PhaseAnalysis:

    def __init__(self, data:pd.DataFrame, elements: Optional[list]):

        self.element = elements
        self.format = data['format'].values
        self.energy = data['energy'].values
        self.get_component(data['format'])


    def get_component(self, symbols):
        import scipy.sparse as ss
        import re

        coords = []

        if self.element != None:
            element = self.element

            for symbol in symbols:
                s = re.findall('([A-Z][a-z]{0,2})([0-9]{0,}\.{0,}[0-9]{0,})', symbol) 
                coord = np.zeros(len(element))
                for e,num in s:
                    if num == '': num = 1.0
                    coord[element.index(e)] = float(num)
                coords.append(coord)

        else:
            raise RuntimeError("Unimplemented function! Please add elements list at present.")

        self.__component = np.array(coords)

    @property
    def component(self):
        return self.__component

    @property
    def normalization_component(self):
        return self.__component / np.sum(self.__component, axis=1)[:,np.newaxis] 


    @classmethod
    def from_csv(cls, filename, elements=None):

        df = pd.read_csv(filename)

        return cls(df, elements)


    def convex_hull(self, index=None, axis:int=0):

        coords = self.normalization_component

        if index != None:
            index = np.array(index)
            coords = coords[index,axis]
            order = index[np.argsort(coords)]
        else:
            assert len(coords[0]) == 2
            coords = coords[:,axis]
            order = np.argsort(coords)

        coords = np.sort(coords)
        energy = self.energy[order]
        xmax = len(energy)
       
        actv = np.argmin(energy)
        stable = [actv]

        while actv != xmax-1 :
            actvx = coords[actv]
            actvy = energy[actv]
            tangs = []
            for i in range(actv+1,xmax):
                tangs.append( (energy[i] - actvy) / (coords[i] - actvx))
            actv += np.argmin(tangs) + 1
            stable.append(actv)
       
        actv = stable[0]
        while actv != 0:
            actvx = coords[actv]
            actvy = energy[actv]
            tangs = []
            for i in range(0,actv):
                tangs.append( (energy[i] - actvy) / (coords[i] - actvx))
            actv = np.argmax(tangs)
            stable.insert(0,actv)

        return order[stable]

    def decompose(self, aim_coord, stables):

        from itertools import combinations
        #print(index, stables)
        results = []

        for points in combinations(stables, len(self.element)):
 
            mat = np.array([self.normalization_component[i] for i in points])
            if nlg.det(mat) == 0: continue
            coeff = np.dot(aim_coord,nlg.inv(mat))
            if np.min(coeff) > -1e-8 and np.max(coeff)-1 <= 1e-8:
                Es = np.array([self.energy[i] for i in points])
                dp = dpath(points, coeff, np.sum(Es*coeff))
                if dp not in results:
                    results.append(dp)

        return results

    def is_stable(self, index, stables):

        coord = self.normalization_component[index]
        energy = self.energy[index]
        dpaths = self.decompose(coord, stables)
        if np.min([i.energy for i in dpaths]) > energy:
            return True

      
    def triangle_zone(self):

        coords = self.normalization_component
        energy = self.energy
        assert len(coords[0]) == 3

        binary = [[], [], []]
        ternary = []
        for i,coord in enumerate(coords):
            is_binary = False
            if energy[i] > 0: continue
            for j,value in enumerate(coord):
                if value == 0:
                    binary[j].append(i)
                    is_binary = True
            if not is_binary:
                ternary.append(i)

        stable = set()
        for i,bin in enumerate(binary):
            #print(self.format[bin])
            bin_stable = self.convex_hull(index=bin, axis=(i+1)%3 )
            #print(self.format[bin_stable])
            stable.update(bin_stable)
        stable = list(stable)

        # print(self.format[stable])

        tri_stable = []
        for i in ternary:
            if self.is_stable(i, stable):
                stable.append(i)
                tri_stable.append(i)

        # print(self.format[stable])

        # check %
        for i in tri_stable[:-1]:
            stable.remove(i)
            if self.is_stable(i, stable):
                stable.append(i)

        # print(self.format[stable])
        return stable

    def convex_hull_diagram(self, stable=None):

        import matplotlib
        matplotlib.use('agg')
        import matplotlib.pyplot as plt

        if stable == None:
            stable = self.convex_hull()

        element = self.element
        coords = self.normalization_component[:,0]
        energy = self.energy
       
        unstable = [ i for i in range(len(energy)) if i not in stable ]
        point_edge = np.array([(coords[i],energy[i]) for i in stable])
        point_float = np.array([(coords[i],energy[i]) for i in unstable])

        plt.figure(figsize=(6,4),dpi=144)
        plt.xlim(0,1)
        ax = plt.gca()
        ax.xaxis.set_tick_params(which='both', direction='in')
        ax.yaxis.set_tick_params(which='both', direction='in')
        ax.set_xticks([0,0.2,0.4,0.6,0.8,1.0])
        ax.set_xticklabels([element[0],0.2,0.4,0.6,0.8,element[1]])
        plt.ylabel('Delta H [eV/atom]')
        plt.xlabel("%s$_{x}$%s$_{1-x}$" %(element[0],element[1]))
        plt.ylim(np.min(point_edge[:,1])*1.1,0)
        plt.grid()
        plt.plot(point_edge[:,0],point_edge[:,1],c='black',linewidth=1)
        plt.scatter(point_float[:,0],point_float[:,1],marker='o',c='',edgecolors='r')
        plt.scatter(point_edge[:,0],point_edge[:,1],marker='o',c='',edgecolors='g')
        plt.savefig('convex_hull.png')

    def triangle_zone_diagram(self, stable=None):

        import matplotlib
        matplotlib.use('agg')
        import matplotlib.pyplot as plt
        import ternary

        if stable == None:
            stable = self.triangle_zone()

        element = self.element
        coords = self.normalization_component
        energy = self.energy
        unstable = [ i for i in range(len(energy)) if i not in stable ]

        figure, tax = ternary.figure(scale=1)
        figure.set_size_inches(5,5)
        tax.boundary(linewidth=1)
        tax.gridlines(multiple=0.1, color="blue")
        tax.ticks(axis='lbr', linewidth=1, multiple=0.2, tick_formats="%.1f", offset = 0.02)
        tax.clear_matplotlib_ticks()
        tax.get_axes().axis('off')
       
        # Plot a few different styles with a legend
        tax.scatter(coords[stable],marker='o',color='',edgecolors='r',s=20, label="Stable")
        tax.scatter(coords[unstable],marker='o',color='',edgecolors='g',s=20, label="Unstable")
        tax.legend()
       
        '''
        for a,b in final_lines:
            for ia,ib in zip(coords[a],coords[b]):
                if ia < 1e-8 and ib < 1e-8:
                    continue
            tax.line(coords[a], coords[b], linewidth=1, marker='', color='black', linestyle=":")
        '''

        # Set Axis labels and Title
        fontsize = 13.5
        tax.right_corner_label('  '+element[0], fontsize=fontsize)
        tax.top_corner_label(' '+element[1], fontsize=fontsize)
        tax.left_corner_label(element[2]+'    ', fontsize=fontsize)
        
        tax.savefig('triangle_zone.png',dpi=144)

    def decompotion_path_output(self, input, stable=None, maximum:int=5, per:str='atom'):

        element = self.element
        if isinstance(input, str):
            s = re.findall('([A-Z][a-z]{0,2})([0-9]{0,}\.{0,}[0-9]{0,})', input) 
            coord = np.zeros(len(element))
            for e,num in s:
                if num == '': num = 1.0
                coord[element.index(e)] = float(num)
            atom_per_formula = np.sum(coord)
            coord /= atom_per_formula

        elif isinstance(input, (list,np.ndarray)):
            if len(list) != len(element):
                raise Exception('The number of elements does not match the length of the input list!')
            atom_per_formula = np.sum(list)
            coord = np.array(list) / atom_per_formula
            
        else:
            raise ValueError('Unknown input data type.')

        if stable == None:
            stable = np.arange(len(self.energy))
        result = self.decompose(coord, stable)

        order = np.argsort([i.energy for i in result])

        print('Decomposition Path of {0} (per {1})'.format(str(input),per))

        record = []
        for i in order:
            dpath = result[i]
            string = " Expect energy : %.4f    " %dpath.energy
            for index, coeff in zip(dpath.output, dpath.coeff):
                if coeff < 1e-8: continue
                if per == 'atom':
                    string += ' {:8s} {:.4f} '.format(self.format[index], coeff)
                elif per == 'formula':
                    coeff = coeff * atom_per_formula / np.sum(self.component[index])
                    string += ' {:8s} {:.4f} '.format(self.format[index], coeff)
            if string not in record:
               print(string)
               record.append(string)
               if len(record) >= maximum:
                   break



                
