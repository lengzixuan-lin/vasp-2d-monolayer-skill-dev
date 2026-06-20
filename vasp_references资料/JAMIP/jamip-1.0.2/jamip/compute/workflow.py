
from abc import ABCMeta, abstractmethod

class WorkFlow(object):
    
    __metaclass__ = ABCMeta
   
    def __init__(self):
        pass 

    def check_status(self):
        pass 

    def optimize(self):
        pass 
    def single_point(self):
        pass 

    def properties(self):
        pass 
    
    def molecular_dynamic(self):
        pass 

    def analysis(self):
        pass


