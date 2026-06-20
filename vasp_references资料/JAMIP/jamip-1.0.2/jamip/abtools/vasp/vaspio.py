
__contributor__ = 'Yawen Li, Dianlong Zhao, Xingang Zhao'
#================================================================
# baisc method for control the input and output 
#================================================================

import os
import numpy as np 

class VaspIO(object):

    def write_poscar(self, structure, stdout=None, name='POSCAR',\
                           direct=True, vasp5=True, **kwargs):
        """
        'comment','constraints','lattice','elements','numbers','type','positions'
        """

        if stdout is None:
            stdout = os.getcwd()

        path = os.path.join(stdout, name)
        
        with open(path, 'w') as f:
            # comment line % 
            f.write(str(structure.comment_line)+'\n')

            # scale line %
            f.write('{0:<16.8f}'.format(structure.scale_factor))
            f.write('\n')
            # lattice lines % 
            for l in structure.lattice:
                f.write(' '.join('{0:>16.8f}'.format(c) for c in l))
                f.write('\n')
            # species line % 
            if vasp5 is True:
                f.write(' '.join('{:>6s}'.format(e) for e in structure.species_of_elements))
                f.write('\n')
                
            # number of elements line %
            f.write(' '.join('{0:>6d}'.format(n) for n in structure.number_of_atoms))
            f.write('\n')
    
            # selective dynamics line %
            if structure.select_dynamic is True:
                f.write('Selective Dynamics\n')

            # direct or casterain line % 
            if direct is True:
                f.write('Direct\n')
                # positiion lines %
                for p in structure.atomic_positions:
                    f.write(' '.join('{0:>16.8f}'.format(j) for j in p.occupation.direct.xyz))
                    if structure.select_dynamic: 
                        f.write('   %s  %s  %s' %p.freeze.xyz)
                    f.write('\n')

            elif direct is False:
                f.write('Cartesian\n')
                # positions lines % 
                for p in structure.atomic_positions:
                    f.write(' '.join('{0:>16.8f}'.format(j) for j in p.occupation.cartesian.xyz))
                    if structure.select_dynamic: 
                        f.write('   %s  %s  %s' %p.freeze.xyz)
                    f.write('\n')

            if structure.initial_velocity is True:
                f.write('\n')
                for p in structure.atomic_positions:
                    f.write(' '.join('{0:>16.8f}'.format(j) for j in p.velocity))
                    f.write('\n')

    @classmethod
    def write_symmetry(cls, structure, stdout=None):
        """
        Output the SYMMETY files for calculate the carriers masses 
            by using Boltzmann method.

        args:
            structure:: Structure object contained the methods get_cell()

            stdout:: the output direction of SYMMETY
        """
        from spglib import get_symmetry

        if stdout is None: stdout = os.getcwd()

        path = os.path.join(stdout, 'SYMMETRY')
        dataset = get_symmetry(structure,symprec=1e-5)['rotations']
        sym = []
        for m in dataset:
            m = m.tolist()
            if m not in sym:
                sym.append(m)

        sym.sort()
        sym.reverse()
        with open(path, 'w') as f:

            f.write("%12d" % (len(sym)))

            for rot in sym:
               for k in rot:
                   f.write('\n')
                   f.write(''.join("%10.5f" % (v) for v in k))
               f.write('\n')

    @classmethod
    def write_potcar(cls, lines, stdout, name='POTCAR'):

        """
        method:: Output the POTCAR in the given direction;

              :param potcar: a dict include the basic info; 
              :param stdout: object direction of POTCAR;

        return True/False
        """
    
        from os.path import join, exists, abspath

        if not exists(abspath(stdout)): 
            os.makedirs(stdout)

        with open(join(stdout, name), 'w') as f:
            f.write(lines)

    def write_kpoints(self,stdout=None,filename='KPOINTS'):
        """
        write out the KPOINTS files if kspacing parameter is None.

        :param kpoints: the object of the kmesh;
        :param stdout: the object path;

        :return: kspacing values if exists.
        """
    
        if stdout is None:
            stdout = os.getcwd()

        path = os.path.join(stdout,filename)

        with open(path,'w') as f:
            f.write('JAMIP KPOINTS\n')

            if self.model == 'Line Model':

                # get insert
                insert = self.kpoints.insert
                if isinstance(insert, list):
                    inset = set(insert) 
                    if len(inset) == 2 and 1 in inset:
                        inset.remove(1)
                        insert = inset.pop()
                        
                if isinstance(insert, int):

                    f.write('%d\n' %insert)
                    f.write(self.model+'\n')
                    f.write('Direct\n')
                    f.write(repr(self.kpoints))

                elif filename != 'KPOINTS':

                    f.write('%d\n '%len(self.kpoints.kpath) )
                    f.write('Direct\n')
                    f.write(self.kpoints.qeformat)
                    
                else:
   
                    raise ValueError('Invalid Kpoints for vasp')

            elif self.model in ['Gamma','Monkhorst-pack']:
                assert self.kpoints.shape == (2,3)
                f.write('0\n')
                f.write(self.model+'\n')
                for i in self.kpoints:
                    f.write(' {0[0]} {0[1]} {0[2]}\n'.format(i))

            elif self.model == 'Reciprocal':
                f.write('%d\n' %len(self.kpoints))
                f.write(self.model+'\n')
                for i in self.kpoints:
                    f.write('{0[0]:14.8f}{0[1]:14.8f}{0[2]:14.8f}    {0[3]}\n'.format(i))

        return {}
 
        # automatically produce the kmesh density %
#        if self.auto_density is True:
#
#            density=self.density/sum(structure.num_atoms)
#            
#            direct_cell=np.transpose(structure.cell)
#            rec_cell=2*np.pi*np.transpose(lalg.inv(direct_cell))
#            
#            b1=np.sqrt(np.dot(rec_cell[0],rec_cell[0]))
#            b2=np.sqrt(np.dot(rec_cell[1],rec_cell[1]))
#            b3=np.sqrt(np.dot(rec_cell[2],rec_cell[2]))
 #           
 #           step=(b1*b2*b3/nkpts)**(1./3)
 #           
 #           n1=int(round(b1/step))
 #           if np.mod(n1,2)!=0: n1=n1-1
 #           n2=int(round(b2/step))
 #           if np.mod(n2,2)!=0: n2=n2-1
 #           n3=int(round(b3/step))
 #           if np.mod(n3,2)!=0: n3=n3-1
 #           
 #           if n1==0:n1=1
 #           if n2==0:n2=1
 #           if n3==0:n3=1
 #         
 #       self.comment = 'Auto density {0}/atom'.format(density) 
 #       self.num = 0  
 #       self.__model = 'Gamma'
 #           self.__kpoints = [[n1, n2, n3],[0., 0.,0.]]
 #
 #       with open(path,'w') as f:
 #           if self.model == 'string':
 #               f.write(kpoints)
 #       return
 #       
 #       f.write(self.comment)
 #           f.write('\n')
 #           if type(self.num) is list:
 #           f.write(' '.join('{0:<5d}'.format(n) for n in self.num))
 #           else:
 #           f.write(' '.join('{0:<5d}'.format(self.num)))
 #           f.write('\n')
 #       f.write(self.model)
 #           f.write('\n')
 #           if self.model == 'Line':
 #               f.write('Direct\n')
 #
 #       for k in self.kpoints:
 #               if self.model == 'Line' or self.model == 'Cartesian' or\
 #           self.model == 'Reciprocal':
 #                   f.write(' '.join('{0:<12.6f}'.format(v) for v in k))
 #               else:
 #                   f.write(' '.join('{0:<6d}'.format(v) for v in k))
 #               f.write('\n')
 
 
    #@classmethod
    def write_kernel(self, stdout=None, name='vdw_kernel.bindat'):
        """Prepare the vdw_kernel"""
 
        import shutil
        from os.path import join, exists

        if stdout == None:
            stdout = os.getcwd()
        elif not exists(stdout):
            os.makedirs(stdout)

        infile = join(os.environ['HOME'],'/.jamip/utils/',name)
        for file in self.external_files:
            if 'kernel.bindat' in file and exists(file):
                infile = file
            
        assert exists(infile) == True
        shutil.copy(infile, stdout)

    @classmethod
    def write_incar(self, incar, stdout=None, **kwargs):
        """
        function: output the INCAR file with format: key = value.
        :param name: output file name, type: string
        :param parses: INCAR input parameters. type: dict
        :param kwargs: external parameter.
        """
        from .tasks import Incar
        from copy import deepcopy

        def format_incar(key, params, total):
            return lines

        if isinstance(incar, dict):
            incar = Incar('incar',incar)
        elif isinstance(incar, Incar):
            incar = deepcopy(incar)
        else:
            raise ValueError('Type of incar params should be dict or Incar!')

        incar.update(kwargs)

        # format information %
        lines = ''
        for key in incar.group:
            if not isinstance(incar.group[key], list): continue
            lines += '\n# %s Parameters\n' %key.upper()
            for i in incar.group[key]:
                if i in incar: 
                    lines += "%-15s = %-s\n" %(i.upper(),incar.pop(i))


        with open(os.path.join(stdout,'INCAR'), 'w') as f:

            for key,value in incar.items():
                if value != None and value != '':
                    f.write("%-15s = %-s\n" %(key.upper(),value))
            f.write(lines)


    def read_kpoint(self, stdin, name='IBZKPT', *args, **kwargs):
       
        import os, numpy
        from kpoints import Kpoints

        kpoints = Kpoints()
        path = os.path.join(stdin, name)
        try:
            with open(path) as f:
                line = f.readline()
                kpoints.comment = line.strip()
                line = f.readline()
                kpoints.num = int(line)
                kpoints.model = f.readline()
                kmesh =[]
                while True:
                    line = f.readline()
                    if not line: break
                    kmesh.append(np.array(line.split()))
                    kpoints.kpoints = kmesh
        except:
            print("Warning: invlaid IBZKPT...")
        finally:
            pass
        
        return kpoints

    def get_eigenvals(self, stdin=None, *args, **kwargs):
        pass

    
    def get_magnomon(self, stdin=None, *args, **kwargs):
        pass
        # print ''.join(line) + \
        # "{0[0]:>20.14f}{0[1]:>20.14f}{0[2]:>20.14f}{1:16.1f}{2:>10s}".format([0.5,0.5,0.5],0.0,'! VBM')+'\n'+\
        # "{0[0]:>20.14f}{0[1]:>20.14f}{0[2]:>20.14f}{1:16.1f}{2:>10s}".format([0.5,0.5,0.0],0.0,'! CBM')
