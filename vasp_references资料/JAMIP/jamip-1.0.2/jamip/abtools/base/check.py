import os
from ruamel import yaml
from os.path import exists, join

class BaseStatus:

    """
    class of task status
    """

    def __load__(self):
        """
        read Status from self.rootdir/.status
        """

        data = None
        if exists(join(self.rootdir, '.status')):
            try:
                with open(join(self.rootdir, '.status'), 'r') as f:
                    data = yaml.load(f,Loader=yaml.RoundTripLoader)
            except:
                pass
        if data == None:
            data = {}

        return data
 
    def __save__(self, data):
        """
        save Status to sale.rootdir/.status
        """

        with open(join(self.rootdir, '.status'), 'w+') as f:
            yaml.dump(data, f, Dumper=yaml.RoundTripDumper, indent=3)


    def write_status(self, status, path):
        """
        base status update function
        """
        data = self.__load__()
        key = os.path.relpath(path, self.rootdir)
        # remove original finish status %
        if status['task'] in ['relax','scf']:
            for i in list(data.keys()):
                if data[i]['task'] == status['task']:
                    data.pop(i)
        # update input status %
        if key in data:
            data.pop(key)
        data[key] = status 

        self.__save__(data)

    def error_status(self, error, path):
        """
        write error task to status 
        """
        data = self.__load__()
        key = os.path.relpath(path, self.rootdir)
        data[key] = {'error':error,'finish':False,'success':False}
        self.__save__(data)

    def right_status(self, tasks):
        """
        update tasks to right
        """
        data = self.__load__()
        if isinstance(tasks, str):
            tasks = [tasks]

        for key,value in data.items():
            if value['task'] in tasks:
                value['finish'] = True
                value['success'] = True
        self.__save__(data)

    def remove_status(self, tasks):
        """
        remove tasks from Status
        """
        data = self.__load__()
        if isinstance(tasks, str):
            tasks = [tasks]

        for i in list(data.keys()):
            if data[i]['task'] in tasks:
                data.pop(i)
        self.__save__(data)


