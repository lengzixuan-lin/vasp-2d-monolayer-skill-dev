
def EspressoPotentials(potdir):
    import os
    if potdir == None or not os.path.isdir(potdir):
        raise IOError("Invalid input Espresso Potential directory!")

    epset = {}
    for file in os.listdir(potdir):
        tmp = file.split('.')
        if tmp[-1] != 'UPF': continue 
        element = tmp[0]
        if element not in epset:
            epset[element] = []
        epset[element].append(file) 

    return epset

class Programs(object):

    def __init__(self):
        self.__program = None 
        self.__files = set()
        self.__pot = None  

    @property
    def potential(self):
        return self.__pot 

    @potential.setter
    def potential(self, value=None):
        self.__pot = value  

    @property 
    def program(self):
        return self.__program 

    @property
    def external_files(self):
        return self.__files

    @program.setter
    def program(self, value=None):
        from os.path import isfile
        if isinstance(value,str) and isfile(value):
            self.__program = value 
        elif isinstance(value, dict):
            self.__program = value
        else:
            raise IOError ('invalid input VASP program')

    @external_files.setter
    def external_files(self,value):
        from os.path import exists,abspath
        import warnings
        if isinstance(value,str) and exists(value):
            self.__files.add(abspath(value))
        elif isinstance(value,(tuple,list)):
            for path in value:
                if exists(path):
                    self.__files.add(abspath(path))
                else:
                    warnings.warn("No external file: %s" %path)
        else:
            raise ValueError("Unsupported input formats for vasp.external_files !")


# basic parameters and defaults setting % 
_CONTROL={\
'calculation':None,
'title':None,
'verbosity':None,
'restart_mode':None,
'wf_collect':None,
'nstep':None,
'iprint':None,
'tstress':None,
'tprnfor':None,
'dt':None,
'outdir':None,
'wfcdir':None,
'prefix':None,
'lkpoint_dir':None,
'max_seconds':None,
'etot_conv_thr':None,
'forc_conv_thr':None,
'disk_io':None,
'pseudo_dir':None,
'tefield':None,
'dipfield':None,
'lelfield':None,
'nberrycyc':None,
'lorbm':None,
'lberry':None,
'gdir':None,
'nppstr':None,
'lfcpopt':None,
'gate':None
}

_SYSTEM = {\
'ibrav':None,
'celldm':None,
'A':None,
'B':None,
'C':None,
'cosAB':None,
'cosAC':None,
'cosBC':None,
'nat':None,
'ntyp':None,
'nbnd':None,
'tot_charge':None,
'starting_charge':None,
'tot_magnetization':None,
'starting_magnetization':None,
'ecutwfc':None,
'ecutrho':None,
'ecutfock':None,
'nr1':None,
'nr2':None,
'nr3':None,
'nr1s':None,
'nr2s':None,
'nr3s':None,
'nosym':None,
'nosym_evc':None,
'noinv':None,
'no_t_rev':None,
'force_symmorphic':None,
'use_all_frac':None,
'occupations':None,
'one_atom_occupations':None,
'starting_spin_angle':None,
'degauss':None,
'smearing':None,
'nspin':None,
'noncolin':None,
'ecfixed':None,
'qcutz':None,
'q2sigma':None,
'input_dft':None,
'ace':None,
'exx_fraction':None,
'screening_parameter':None,
'exxdiv_treatment':None,
'x_gamma_extrapolation':None,
'ecutvcut':None,
'nqx1':None,
'nqx2':None,
'nqx3':None,
'localization_thr':None,
'lda_plus_u':None,
'lda_plus_u_kind':None,
'Hubbard_U':None,
'Hubbard_J0':None,
'Hubbard_V':None,
'Hubbard_alpha':None,
'Hubbard_beta':None,
'Hubbard_J':None,
'starting_ns_eigenvalue':None,
'U_projection_type':None,
'Hubbard_parameters':None,
'ensemble_energies':None,
'edir':None,
'emaxpos':None,
'eopreg':None,
'eamp':None,
'angle1':None,
'angle2':None,
'lforcet':None,
'constrained_magnetization':None,
'fixed_magnetization':None,
'lambda':None,
'report':None,
'lspinorb':None,
'assume_isolated':None,
'esm_bc':None,
'esm_w':None,
'esm_efield':None,
'esm_nfit':None,
'fcp_mu':None,
'vdw_corr':None,
'london':None,
'london_s6':None,
'london_c6':None,
'london_rvdw':None,
'london_rcut':None,
'dftd3_version':None,
'dftd3_threebody':None,
'ts_vdw_econv_thr':None,
'ts_vdw_isolated':None,
'xdm':None,
'xdm_a1':None,
'xdm_a2':None,
'space_group':None,
'uniqueb':None,
'origin_choice':None,
'rhombohedral':None,
'zgate':None,
'relaxz':None,
'block':None,
'block_1':None,
'block_2':None,
'block_height':None
}

_ELECTRONS={\
'electron_maxstep':None,
'scf_must_converge':None,
'conv_thr':None,
'adaptive_thr':None,
'conv_thr_init':None,
'conv_thr_multi':None,
'mixing_mode':None,
'mixing_beta':None,
'mixing_ndim':None,
'mixing_fixed_ns':None,
'diagonalization':None,
'diago_thr_init':None,
'diago_cg_maxiter':None,
'diago_david_ndim':None,
'diago_full_acc':None,
'efield':None,
'efield_cart':None,
'efield_phase':None,
'startingpot':None,
'startingwfc':None,
'tqr':None,
'real_space':None,
}

_IONS={\
'ion_positions':None,
'ion_velocities':None,
'ion_dynamics':None,
'pot_extrapolation':None,
'wfc_extrapolation':None,
'remove_rigid_rot':None,
'ion_temperature':None,
'tempw':None,
'tolp':None,
'delta_t':None,
'nraise':None,
'refold_pos':None,
'upscale':None,
'bfgs_ndim':None,
'trust_radius_max':None,
'trust_radius_min':None,
'trust_radius_ini':None,
'w_1':None,
'w_2':None,
}

_CELL ={\
'cell_dynamics':None,
'press':None,
'wmass':None,
'cell_factor':None,
'press_conv_thr':None,
'cell_dofree':None,
}

def pwscf_format(params):

    control = {}
    system = {}
    electrons = {}
    ions = {}
    cell = {}
    for key,value in params.items():

        # value %
        if value == None:
            print("Error: The value of the key '%s' \
                            shouldn't be None" % key)
            continue
        elif value == '':
            print("Error: The key '%s' should have \
                                    a value." % key)
            continue
        elif isinstance(value,float):
            value = ('%e' %params[key]).replace('e','d')
        elif key == 'calculation':
             pass
        elif isinstance(value,str):
            value = "'%s'" %value

        # key %
        if key in _CONTROL:
            control[key] = value
        elif key in _SYSTEM:
            system[key] = value
        elif key in _ELECTRONS:
            electrons[key] = value
        elif key in _IONS:
            ions[key] = value
        elif key in _CELL:
            cell[key] = value
        else:
            print("Invalid key %s in pwscf.in ." %key)

    return control, system, electrons, ions, cell

class KeyWords(object):

  def __init__(self, **kwargs):
       params = __incar__
       params.update(kwargs)
       self.__set_keywords__(params)


  def __set_keywords__(self, params=None):
       for key in params:
           if key not in self.__dict__:
               is_set = False
               for k in params[key]: 
                   if params[key][k] is not None: 
                       is_set = True
               if is_set: 
                   self.__dict__[key] = self.__parameters__(params[key])
  
  def __parameters__(self, name):
	
        class Parameters(object):
            pass 
        p = Parameters()
        for key in name:
            if key not in p.__dict__ and name[key] is not None:
                p.__dict__[key] = name[key]
	
        return p


def dict_get(dict, key, default):
    tmp = dict
    for k,v in tmp.items():
        if k == key:
            return v
        else:
            if type(v) is types.DictType:
                ret = dict_get(v, key, default)
                if ret is not default:
                    return ret
    return default

   

# %%%%%%%%%%% appendix code %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#         symobl   z    mass        wfc     rho 
EspressoElements = {\
          'H'  :[  1,   1.007825,    60,   480],
          'He' :[  2,   4.002602,    50,   200],
          'Li' :[  3,   6.938,       40,   320],
          'Be' :[  4,   9.012182,    40,   320],
          'B'  :[  5,  10.806,       35,   280],
          'C'  :[  6,  12.0096,      45,   360],
          'N'  :[  7,  14.00643,     60,   480],
          'O'  :[  8,  15.99903,     50,   400],
          'F'  :[  9,  18.9984032,   45,   360],
          'Ne' :[ 10,  20.1797,      50,   200],
          'Na' :[ 11,  22.98976928,  40,   320],
          'Mg' :[ 12,  24.304,       30,   240],
          'Al' :[ 13,  26.9815386,   30,   240],
          'Si' :[ 14,  28.084,       30,   240],
          'P'  :[ 15,  30.973762,    30,   240],
          'S'  :[ 16,  32.059,       35,   280],
          'Cl' :[ 17,  35.446,       40,   320],
          'Ar' :[ 18,  39.948,       60,   240],
          'K'  :[ 19,  39.0983,      60,   480],
          'Ca' :[ 20,  40.078,       30,   240],
          'Sc' :[ 21,  44.955912,    40,   160],
          'Ti' :[ 22,  47.867,       35,   280],
          'V'  :[ 23,  50.9415,      35,   280],
          'Cr' :[ 24,  51.9961,      40,   320],
          'Mn' :[ 25,  54.938045,    65,   780],
          'Fe' :[ 26,  55.845,       90,  1080],
          'Co' :[ 27,  58.933195,    45,   360],
          'Ni' :[ 28,  58.6934,      45,   350],
          'Cu' :[ 29,  63.546,       55,   440],
          'Zn' :[ 30,  65.38,        40,   320],
          'Ga' :[ 31,  69.723,       70,   560],
          'Ge' :[ 32,  72.63,        40,   320],
          'As' :[ 33,  74.9216,      35,   280],
          'Se' :[ 34,  78.96,        30,   240],
          'Br' :[ 35,  79.901,       30,   240],
          'Kr' :[ 36,  83.798,       45,   180], 
          'Rb' :[ 37,  85.4678,      30,   120],
          'Sr' :[ 38,  87.62,        30,   240],
          'Y'  :[ 39,  88.90585,     35,   280],
          'Zr' :[ 40,  91.224,       30,   240],
          'Nb' :[ 41,  92.90638,     40,   320],
          'Mo' :[ 42,  95.96,        35,   140],
          'Tc' :[ 43,  97.90721,     30,   120],
          'Ru' :[ 44, 101.07,        35,   140],
          'Rh' :[ 45, 102.9055,      35,   140],
          'Pd' :[ 46, 106.42,        45,   180],
          'Ag' :[ 47, 107.8682,      50,   200],
          'Cd' :[ 48, 112.41,        60,   480],
          'In' :[ 49, 114.818,       50,   400],
          'Sn' :[ 50, 118.71,        60,   480],
          'Sb' :[ 51, 121.76,        40,   320],
          'Te' :[ 52, 127.6,         30,   240],
          'I'  :[ 53, 126.90447,     35,   280],
          'Xe' :[ 54, 131.293,       60,   240],
          'Cs' :[ 55, 132.9054519,   30,   240],
          'Ba' :[ 56, 137.327,       30,   240],
          'La' :[ 57, 138.90547,     40,   320],
          'Ce' :[ 58, 140.116,       40,   320],
          'Pr' :[ 59, 140.90765,     40,   320],
          'Nd' :[ 60, 144.242,       40,   320],
          'Pm' :[ 61, 144.91276,     40,   320],
          'Sm' :[ 62, 150.36,        40,   320],
          'Eu' :[ 63, 151.964,       40,   320],
          'Gd' :[ 64, 157.25,        40,   320],
          'Tb' :[ 65, 158.92535,     40,   320],
          'Dy' :[ 66, 162.5,         40,   320],
          'Ho' :[ 67, 164.93032,     40,   320],
          'Er' :[ 68, 167.259,       40,   320],
          'Tm' :[ 69, 168.93421,     40,   320],
          'Yb' :[ 70, 173.054,       40,   320],
          'Lu' :[ 71, 174.9668,      45,   360],
          'Hf' :[ 72, 178.49,        50,   200],
          'Ta' :[ 73, 180.94788,     45,   360],
          'W'  :[ 74, 183.84,        30,   240],
          'Re' :[ 75, 186.207,       30,   240],
          'Os' :[ 76, 190.23,        40,   320],
          'Ir' :[ 77, 192.217,       55,   440],
          'Pt' :[ 78, 195.084,       35,   280],
          'Au' :[ 79, 196.966569,    45,   180],
          'Hg' :[ 80, 200.592,       50,   200],
          'Tl' :[ 81, 204.382,       50,   400],
          'Pb' :[ 82, 207.2,         40,   320],
          'Bi' :[ 83, 208.9804,      45,   360],
          'Po' :[ 84, 209.0,         75,   600],
          'At' :[ 85, 210.0,         50,   600],
          'Rn' :[ 86, 222.0,        120,   960],
}
