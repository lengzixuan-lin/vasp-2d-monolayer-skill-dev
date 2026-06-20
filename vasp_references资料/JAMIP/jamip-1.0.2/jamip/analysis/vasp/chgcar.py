import os
import numpy as np

class GrepChgcar(object):

    def __init__(self):
        pass

    def poscar_info(self,input):
        
        # comment
        comment=''
        string=input.readline()
        if string != "":
            comment = string.strip()
            
        scale=float(input.readline())
        
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
        type=''
        if tmp.lower().startswith('s'): # Selective dynamics
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
        for i in range(0, natoms):
            try:
                string=input.readline().split()
                positions.append(np.array(string[:3],dtype='float'))
            except ValueError:
                ("can't transfer literal to float type!")
                exit()
        positions=np.array(positions)
        if type == 'Cartesian':
            positions = positions*scale

        poscar={'comment':comment,
                'lattice':lattice,
                'elements':elements,
                'numbers':numbers,
                'type':type,
                'positions':positions}
        return poscar,input

    def chgcar(self,path='.',filename="CHG"):
        # print(path+'/'+filename)
        fopen = open(path+'/'+filename,'r')
        info,fopen = self.poscar_info(fopen)
        
        for line in fopen:
            if len(line.split()) == 3:
                shape = np.array(line.split(),dtype=int)
                break

        data = []
        for line in fopen:  
            if len(line.split()) > 0:
                data.extend(line.split())
        data = np.array(data,dtype=float)
        assert data.size == shape[0]*shape[1]*shape[2]
        return info,data.reshape(shape[::-1]).transpose(2,1,0)

    def chgcar_sum(self,path=None,output=None,file='CHGCAR_sum',\
                   file1="AECCAR0",file2="AECCAR2"):
        if path is None: path = os.getcwd()
        if output is None: output = path
        info1,data1 = self.chgcar(path,file1)
        info2,data2 = self.chgcar(path,file2)

        data = data1+data2
        self.write_chgcar(info1,data,output,file)

    def write_chgcar(self,info,data,path='.',filename='CHGCAR'):
        with open(path+'/'+filename,'w') as f:
            # comment line %
            f.write(info["comment"]+'\n')
            # scale line %
            f.write('  1.0\n')
            # lattice lines %
            for l in info["lattice"]:
                f.write(''.join('{0:>16.8f}'.format(c) for c in l))
                f.write('\n')
            # species line %
            f.write(' '.join('{0:>5s}'.format(e) for e in info['elements']))
            f.write('\n')
            # number of elements line %
            f.write(' '.join('{0:>5d}'.format(n) for n in info['numbers']))
            f.write('\n')
            # direct or casterain line % 
            f.write(info['type']+'\n')
            for p in info['positions']:
                f.write(''.join('{0:>16.8f}'.format(j) for j in p))
                f.write('\n')
            # blank line %
            f.write('\n')
            # data shape line %
            f.write(' '.join('{0:>5d}'.format(n) for n in data.shape))
            f.write('\n')
            # chgcar lines %
            tmp = 0 
            data = data.reshape(-1)
            while tmp < data.size:
                f.write(''.join('{0:>18.10E}'.format(n) for n in data[tmp:tmp+5]))
                f.write('\n')
                tmp += 5
                
                
