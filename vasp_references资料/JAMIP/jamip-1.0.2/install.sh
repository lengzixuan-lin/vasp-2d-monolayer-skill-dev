#!/bin/bash

#pip3 install psutil django phonopy mendeleev matplotlib numpy scipy scikit-learn seaborn ruamel.yaml==0.16 -i https://pypi.douban.com/simple/
python3 setup.py build 
python3 setup.py install --user

echo 'export PATH=~/.jamip/bin:$PATH ' >> $HOME/.bashrc
source $HOME/.bashrc
