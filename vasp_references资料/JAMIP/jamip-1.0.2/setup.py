import shutil
from setuptools import find_packages
from numpy.distutils.core import setup, Extension
from os.path import exists,join,relpath
import os
import sys
import stat

HOME = os.environ['HOME']
JAMIPPATH = HOME+'/.jamip'
PYTHONPATH = os.popen('which python3').readline()

# copy .jamip to HOME %
#if exists(join(HOME,'.jamip')):
#    shutil.rmtree(join(HOME,'.jamip'))
if not exists(join(HOME,'.jamip')):
    shutil.copytree('source/config',join(HOME,'.jamip'))

# copy jp with RWX %
with open(HOME+'/.jamip/bin/jp','w') as f:
    f.write('#!'+PYTHONPATH+'\n')
    f.write('# -*- coding: utf-8 -*-\n')
    f.write('import jamip \n')
    f.write('from jamip.cui.script import runjamip\n\n')
    f.write('runjamip() ')
os.chmod(HOME+'/.jamip/bin/jp',stat.S_IRWXU)    

# jamip packages.
JAMIP = 'jamip'
PACKAGES = [JAMIP] + ['%s.%s' % (JAMIP, i) for i in find_packages(JAMIP)]
SOURCE = ['install.sh']#, 'JAMIP-V1.0.Manual-Chs.pdf']
for path, dirs, files in os.walk('source'):
    for f in files:
        SOURCE.append(join(relpath(path,os.getcwd()),f))

setup(name = 'jamip',
      version = '1.0.2',
      license = 'Jilin University',
      description = 'Python Package for HTP calculation.',
      author = 'Xin-Gang Zhao',
      author_email = 'admin@jamip-code.cn',
      url = 'http://www.jamip-code.dn',
      packages = PACKAGES,
      package_data={'':['*.csv']},
      data_files = [('jamipenv', SOURCE)],
      ext_modules= [
          Extension(name='jamip.analysis.vasp.fmsd',sources=['source/fmsd.f90'])
      ],
      install_requires=[
          'scikit-learn >= 0.22',
          'ruamel.yaml >= 0.16',
          'ipython >= 2.0',
          'django >= 3.1',
          'numpy >= 1.14',
          'scipy >= 1.4',
          'matplotlib',
          'mendeleev',
          'phonopy',
          'psutil',
          'seaborn']
      )

