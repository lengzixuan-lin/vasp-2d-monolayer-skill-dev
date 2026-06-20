import numpy as np
from functools import lru_cache

class BondAtom(object):
   
    def __init__(self,Bond,kid,bonds):
        self.origin = (kid,bonds)
        self.kernel = Bond.elements[kid]
        self.position = Bond.direct_positions[kid]
        # create datas %
        self._bond_e = [Bond.elements[bid] for bid in bonds]
        self._bond_d = [Bond.distances[kid][bid] for bid in bonds]
        self._bond_c = [Bond.direct_positions[bid] for bid in bonds]
        del Bond

    def get_bondlen(self,type='mean'):
        if type == 'mean':
            return self.meanbond
        elif type == 'min':
            return self.minbond
            
    @property
    def minbond(self):
        return np.min(self._bond_d)

    @property
    def meanbond(self):
        return np.mean(self._bond_d)

    @property
    def environment(self):
        env = {}
        for atom in self._bond_e:
            if atom not in env:
                env[atom] = 1
            else :
                env[atom] += 1
        envstr = ''
        envsort = np.sort(list(env.keys()))
        for atom in envsort:
            if env[atom] >1:
                envstr += '%s%d' %(atom,env[atom])
            else:
                envstr += atom
        return envstr

    def __repr__(self):
        return self._print

    @property
    def _print(self):
        prints = []
        prints.append('\nAtom:{0:2s}  tot:{1} '.format(self.kernel,len(self._bond_d)))
        for atom,distance in zip(self._bond_e,self._bond_d):
            prints.append('{0:>2s} : {1:.4f}'.format(atom,distance))
        return '  '.join(prints)

class Bonding(object):

    _check = True    

    def __init__(self,structure,bondrange=0.3,**kwargs):
        self.bondrange = bondrange
        # load structure %
        self.species = structure.species_of_elements
        self.elements = structure.get_elements(type='symbol')
        self.distances = structure.get_all_distances(min=True)
        self.positions = np.dot(structure.get_positions(),structure.lattice)
        # load structure 2 %
        self.direct_positions = structure.get_positions()
        self.lattice = structure.lattice
        # create 3*3 supercell %
        self.vector = self.get_vector(structure.lattice)
        if 'radius' in kwargs:
            self._radius = kwargs.pop('radius')
            if 'vasp' in kwargs and kwargs['vasp'] == True:
                self.build_with_radius_vasp()
            else:
                self.build_with_radius()
        else:
            self.build_with_range()

    @lru_cache()
    def getRadius(self,elm1,elm2,min=False):
        rs = []
        rsum = 0
        for elm in [elm1,elm2]:
            if elm not in self._radius:
                raise KeyError("Invalid Element %s!" %elm)
            elif isinstance(self._radius[elm],dict):
                for tag in ['_3','_2','','_sv','_pv','_d','_s','_h']:
                    if elm+tag in self._radius[elm]:
                        rs.append(self._radius[elm][elm+tag])
                        break
            else:
                rs.append(self._radius[elm])

        assert len(rs) == 2
        rsum = np.sum(rs)*1.2
        rmin = np.min(rs)*1.2
        #print(elm1,elm2,rsum)
        if min == True:
            return rsum,rmin
        else:
            return rsum

    def build_with_radius_vasp(self):
        import warnings
        bondset = []
        rmin = np.min([self.getRadius(elm,elm)/2 for elm in self.species])
        for i,elm1 in enumerate(self.elements):
            bonds = []
            for j,elm2 in enumerate(self.elements):
                if i == j: continue
                rsum = self.getRadius(elm1,elm2)
                distance = self.distances[i][j]
                # get atoms under radius range %
                if distance < rsum:
                    bonds.append(j)
                    if self._check and distance < rmin:
                        warnings.warn('rwigs warning!')
                        self._check = False

            # get nearest atoms ids %
            allbonds = self.get_equal(i,bonds)
            bondset.append(BondAtom(self,i,allbonds))
        # save property %
        self.data = bondset

    def build_with_radius(self):
        import warnings
        bondset = []
        for i,elm1 in enumerate(self.elements):
            bonds = []
            for j,elm2 in enumerate(self.elements):
                if i == j: continue
                rsum,rmin = self.getRadius(elm1,elm2,min=True)
                distance = self.distances[i][j]
                # get atoms under radius range %
                if distance < rsum:
                    bonds.append(j)
                    if self._check and distance < rmin:
                        warnings.warn('rwigs warning!')
                        self._check = False
            # get nearest atoms ids %
            allbonds = self.get_equal(i,bonds)
            bondset.append(BondAtom(self,i,allbonds))
        # save property %
        self.data = bondset

    def build_with_range(self):
        bondset = []
        for i in range(self.distances.shape[0]):
            # get nearest atoms %
            bmin = None
            num = 1
            for bondlen in np.sort(self.distances[i])[1:]:
                if bmin == None:
                    bmin = bondlen
                elif bondlen-bmin > self.bondrange:
                    break
                num += 1

            # get nearest atoms ids %
            bonds = np.argsort(self.distances[i])[1:num]
            allbonds = self.get_equal(i,bonds)
            bondset.append(BondAtom(self,i,allbonds))
        # save property %
        self.data = bondset

    def get_minbond(self):
        minlen = 1000
        mintype = None
        for dat in self.data:
            for e,d in zip(dat._bond_e,dat._bond_d):
                if d < minlen:
                    minlen = d
                    mintype = tuple(set((dat.kernel,e)))

        return minlen,mintype

  
    def get_vector(self,lattice):
        vector=np.zeros(3)
        for i in lattice:
            vector=np.vstack((vector,vector+i,vector-i))
        return vector

    def get_equal(self,kid,bids):
        bondlist = []
        kernel = self.positions[kid]
        for bid in bids:
            bond = self.positions[bid]
            bondlen = self.distances[kid][bid]
            if np.linalg.norm(kernel-bond) - bondlen > 1e-8:
                equal = 0
            else: equal = 1
            for v in self.vector[1:]:
                if np.linalg.norm(kernel-bond+v) - bondlen < 1e-8:
                    equal += 1
            if equal > 0:
                bondlist.extend([bid]*equal)
        bondlist = np.array(bondlist)
        return bondlist

    def get_bond_by_kernel(self,atoms,bondtype='mean'):
        if isinstance(atoms,str): atoms=[atoms]
        envs = {}
        # get bonds step %
        for dat in self.data:
            if dat.kernel not in atoms: continue
            if dat.kernel not in envs: envs[dat.kernel] = []
            env_format = dat.environment
            env_bondlen = dat.get_bondlen(bondtype)
            envs[dat.kernel].append((env_format,env_bondlen))

        # get print step  %
        prints = []
        for kernel,dat in envs.items():
            prints.append('-------------\nAtom:{0:2s}  tot:{1} '.format(kernel,len(dat)))
            atomenv = {}
            for format,distance in dat:
                if format not in atomenv: atomenv[format] = []
                atomenv[format].append(distance)

            for format in atomenv:
                if bondtype == 'mean': bondlen = np.mean(atomenv[format])
                elif bondtype == 'min': bondlen = np.min(atomenv[format])
                prints.append('type:{0:8s}  {3}bond:{1:.4f}   tot:{2}'.format(format,bondlen,len(atomenv[format]),bondtype))

        return '\n'.join(prints)

    def get_bond_by_orient(self,pairs,orient,bondtype='mean'):
        # set pair % 
        if isinstance(pairs[0],(list,tuple)):
            for pair in pairs:
                pairs = [set(i) for i in pairs]
        elif isinstance(pairs,(list,tuple)):
            pairs = [set(pairs)]
        # check orient %
        assert len(orient) == 3
        
        # seek pair %
        bondlens = []
        for pair in pairs:
            bondlen_T = []
            bondlen_F = []
            for dat in self.data:
                if dat.kernel not in pair: continue
                for e,d,coord in zip(dat._bond_e,dat._bond_d,dat._bond_c):
                    if set((dat.kernel,e)) == pair:
                        vector = [v-round(v) for v in coord-dat.position]
                        cosangle = np.dot(orient,vector)/(np.linalg.norm(vector)*np.linalg.norm(orient))
                        if abs(cosangle)-1 > -1e-3:
                            bondlen_T.append(d)
                        else:
                            bondlen_F.append(d)
            bondlens.append((bondlen_T,bondlen_F))
        
        # get print %
        prints = []
        for pair,dats in zip(pairs,bondlens):
            for label,dat in zip(['T','F'],dats):
                # Remove duplicate %
                if len(pair) == 1: tot = len(dat)
                else: tot = int(len(dat)/2)
                # ccal bondlen %
                if bondtype == 'mean': bondlen = np.mean(dat)
                elif bondtype == 'min': bondlen = np.min(dat)
                prints.append('type:{0:6s}  bond:{1:.4f}  tot:{2} '.format('-'.join(list(pair))+'-'+label,bondlen,tot))

        return '\n'.join(prints)

    def get_bond_by_pair(self,pairs,bondtype='mean'):
        if isinstance(pairs[0],(list,tuple)):
            for pair in pairs:
                pairs = [set(i) for i in pairs]
        elif isinstance(pairs,(list,tuple)):
            pairs = [set(pairs)]

        # seek pair %
        bondlens = []
        for pair in pairs:
            bondlen = []
            for dat in self.data:
                if dat.kernel not in pair: continue
                for e,d in zip(dat._bond_e,dat._bond_d):
                    if set((dat.kernel,e)) == pair:
                        bondlen.append(d)
            bondlens.append(bondlen)

        # get print %
        prints = []
        for pair,dat in zip(pairs,bondlens):
            # Remove duplicate %
            if len(pair) == 1: tot = len(dat)
            else: tot = int(len(dat)/2)
            # ccal bondlen %
            if bondtype == 'mean': bondlen = np.mean(dat)
            elif bondtype == 'min': bondlen = np.min(dat)
            prints.append('type:{0:6s}  bond:{1:.4f}  tot:{2} '.format('-'.join(list(pair)),bondlen,tot))

        return '\n'.join(prints)
