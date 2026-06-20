"=========================================================="
"introduction of functions:" \
"runtime: show the running time of the script" \
"FindKeys: find the keyword in the given line"
""
def runtime():
    import time as tm
    return tm.strftime("%Y-%m-%d %H:%M:%S",tm.localtime(tm.time()))

def FindKeys(key, line, upper_key=False):

    """
    functional to get the value from the given string for the given keyword.
    :parameter
    key: the given keyword;
    line: the object string;
    """

    import re
    value = None

    if upper_key: key=key.upper()
    obj = ''.join(line)
    try:
        # float or integer%
        value = re.findall(r'{0}\s*=\s*\-?\d*\.?\d+'.format(key), obj)
        value = float(value[0].split()[-1])

    except:
        try:
            # bool type and characters%
            value = re.findall(r'{0}\s*=\s*\S+'.format(key.upper()), obj)
            value = value[0].split()[-1].strip(';')
            if 'true' in value.lower() or value.lower() == 't':
                value = True
            if 'false' in value.lower() or value.lower() == 'f':
                value = False
        except:
            pass
    finally:
        pass
    return {key: value}

class CopyFile(object):
    """class to copy files
    static method: loop_files;
    method: load_files:
    """
    import os

    def load_files(self, stdin, stdout, loop=False, include=None, exclude=None):
        """
        load_files: copy file from 'stdin' directory to 'stodut' directory;
        :param stdin: the original directory includes the files wait for copy;
        :param stdout: the object directory;
        :param loop: bool, directory or documents, False: documents;
        :param include: given files to copies;
        :param exclude: given files to ignore;
        :return: None
        """

        if not os.path.exists(stdout): os.makedirs(stdout)
        if include is not None:
            for f in include:
               src = os.path.join(stdin, f)
               os.system('cp -r {0} {1}'.format(src,stdout))
        return
        n=2
        if loop is Ture: n = 1
        copyfile = os.walk(stdin).next()[n]

        if exclude is not None:
            for exf in exclude:
                if exf in copyfile:
                    copyfile.remove(exf)
        
        for f in copyfile:
            src = os.path.join(stdin, f)
            os.system('cp -r {0} {1}'.format(src,stdout))
 
