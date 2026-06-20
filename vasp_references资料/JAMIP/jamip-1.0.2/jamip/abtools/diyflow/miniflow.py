from jamip.abtools.vasp.vaspflow import VaspFlow

class MiniFlow(VaspFlow):

    def __init__(self, vasp=None, stdin=None, rootdir=None, *args, **kwargs):

        from os.path import dirname,join
        from jamip.compute.cluster import Cluster
    
        self.stdin = stdin
        self.rootdir = rootdir
        self.cluster = Cluster(dirname(dirname(rootdir)))
	
    def diy_calculator(self, vasp, stdout, stdin=None, **kwargs):
        
        print('Default calculator.')

    @classmethod
    def check(self,root):
        
        print('check diy task finish.')
        return True
  
    def create_input(self, vasp, stdout=None, stdin=None, incar={}, overwrite=True, **kwargs):

        from jamip.structure import read 
        from os.path import join, exists, getsize 
        import shutil
        import os  

        # restart from previous calculation % 
        if stdin is None:
               incar['istart'] = 0
               incar['icharg'] = 2
        elif stdin is not None:

            # skip udpate the structure % 
            if stdin != stdout:
                if not exists(stdout): os.makedirs(stdout)
                overwrite = True 

                # copy chgcar %
                chgin = join(stdin,'CHGCAR')
                chgout = join(stdout,'CHGCAR')
                if exists(chgin) and getsize(chgin):
                    if 'icharg' not in incar:
                        incar['icharg'] = 1
                elif 'icharg' not in incar:
                    incar['icharg'] = 2
                elif incar['icharg'] == 11:
                    raise IOError('CHGCAR not exists!')

                if incar['icharg'] == 1 or incar['icharg'] == 11:
                    if 'lcharg' in incar and incar['lcharg'] is False:
                        if exists(chgout): os.remove(chgout)
                        os.symlink(chgin,chgout)
                    else:
                        shutil.copyfile(chgin,chgout)

                # copy wavecar %
                wavein = join(stdin,'WAVECAR')
                waveout = join(stdout,'WAVECAR')
                if exists(wavein) and getsize(wavein):
                    if 'istart' not in incar:
                        incar['istart'] = 1
                else:
                    incar['istart'] = 0

                if incar['istart'] == 1:
                    if 'lwave' in incar and incar['lwave'] is False:
                        if exists(waveout): os.remove(waveout)
                        os.symlink(wavein,waveout)
                    else:
                        shutil.copyfile(wavein,waveout)

        incar = vasp.set_input(vasp.structure, stdout, overwrite, incar)

        # update vasp program %
        if isinstance(vasp.program, dict):
            if 'lsorbit' in incar or'LSORBIT' in incar:
                program = vasp.program['ncl'] 
            else:
                raise KeyError('Non-collinear version of the VASP is required for SOC calculations')
        else:
            program = vasp.program

        return stdout,program
