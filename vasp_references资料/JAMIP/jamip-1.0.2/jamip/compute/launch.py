
class __LaunchTasks(object):

    def __init__(self, params=None, *args, **kwargs):
        
        if params['run']  == 'prepare':
            params.pop('run')
            self.__prepare__(params)

        elif params['run']  == 'qsub':
            params.pop('run')
            self.__launch__(params,*args)

        elif params['run']  == 'single':
            params.pop('run')
            self.__single__(params,*args)

    def __prepare__(self, params=None, *args, **kwargs):

        # create pool %
        try:
            import sys,os
            if os.path.isfile('input.py'):
                sys.path.append(os.getcwd())
                from input import jamip_input 
            else:
                raise IOError ('input.py not exists..')
        except:
            raise IOError ('please construct input.py firstly..')

        jamip_input(params)  
	 
	
    def __launch__(self, params=None, *args, **kwargs):
	
        # load pool %
        import os
        from os.path import abspath, join, exists 
        from .cluster import Cluster
        from .pool import Pool
        import socket

        root = os.getcwd()

        poolfile = abspath(params['pool'])
        p = Pool().loader(poolfile)
		
        # load cluster %
        cluster = Cluster(root)

        # check cluster environment % 
        if 'cluster' in params:
            cluster.update(params['cluster'])
        cluster['user'] = os.environ['USER']
        cluster['host'] = socket.gethostname() 

        # check maximum number of tasks %
        if 'maximum' in params:
            cluster['maximum'] = params['maximum']

        # check restart/overwrite % 
        if 'overwrite' in params and params['overwrite']:
            cluster['overwrite'] = True
 
        if 'restart' in params and params['restart']:
            cluster['restart'] = True

        # update task status %
        if len(args) > 0:
            for outdir in args:
                p.pool[outdir]['status'] = 'finish'
        else:
            cluster.__dump__(root)

        # qsub the jobs % 
        n = 1
	
        # according to the prior order %  
        for outdir in sorted(p.pool.items(),key=lambda v:v[1]['prior']):

            # get the default setting and update setting %  
            if n > cluster.maximum: break
            outdir = outdir[0]              # relative path & key % 
            if p.pool[outdir]['status'] == 'wait' and (p.pool[outdir]['prior'] != -1 or cluster.restart is True):
                stdout = join(root,outdir)      # absolute path %
                if not exists(stdout): 
                    os.makedirs(stdout)
                elif cluster.restart and exists(stdout+'/.status'):
                    self.__restart__(stdout)

                # tag the task status % 
                os.system('touch %s/.wait' %stdout) 
                # submit the jobs % 	
                os.chdir(stdout)
                cluster.submit(poolfile,outdir)
                os.chdir(root)
                if len(cluster.index):
                    print(cluster.index)
                else:
                    raise IOError('Failed to submit task')
                p.job_id=cluster.index[0]

                p.pool[outdir]['prior']  -= 1
                p.pool[outdir]['status']  = 'running'
                p.pool[outdir]['job_id']  = p.job_id
                
                n += 1     		
            else:
                print('task in {0} is: '.format(outdir), p.pool[outdir]['status'])

        p.save(poolfile,**p.pool)
	
	

    def __single__(self, params, root=None, outdir=None):
	
        import os 
        import time
        from os.path import join,abspath,exists
        from .pool import Pool
        from .single import SingleManager 

        if root is None:
            root = os.getcwd()

        poolfile = abspath(params['pool'])
        p = Pool().loader(poolfile)
        single = SingleManager(root)

        # check restart/overwrite % 
        if 'overwrite' in params:
            overwrite = True
        else:
            overwrite = False
 
        if 'restart' in params:
            restart = True 
        else:
            restart = False  

        for outdir in sorted(p.pool.items(),key=lambda v:v[1]['prior']):

	    # get the default setting and update setting %  
            outdir = outdir[0] 
            if p.pool[outdir]['status'] == 'wait' and (p.pool[outdir]['prior'] != -1 or restart is True):
                print(p.pool[outdir]['status'],restart,outdir)
                stdout = join(root, outdir)
                if not exists(stdout): 
                   os.makedirs(stdout)
                elif restart and exists(stdout+'/.status'):
                    os.system('rm %s/.status' %stdout) 
                    self.__restart__(stdout)
                func = p.pool[outdir]['functional']
                func.overwrite = overwrite
                
                # submit the jobs % 
                os.chdir(stdout)
                os.system('touch %s/pbsscript' %stdout) 
                status = single.submit(func,stdout)
                os.chdir(root)

                p.pool[outdir]['prior']  -= 1
                p.pool[outdir]['job_id']  = 0
                if status:
                    p.pool[outdir]['status']  = 'finish'
                else:
                    p.pool[outdir]['status']  = 'running'
                func.tasks = eval(func.tasks.__repr__())
	        
            else:
                print('task in {0} is: '.format(outdir), p.pool[outdir]['status'])
	
        p.save(poolfile,**p.pool)
	
    def __restart__(self, outdir=None):

        # rm WAVECARs, CHGCARs %	
        import os 

        # find files %
        os.remove(os.path.join(outdir,'.status')) 
        for filename in ['CHG','CHGCAR','WAVECAR']:
            files = os.popen("find %s -name %s" %(outdir,filename))
            for f in files:
                fhead = os.path.relpath(f,outdir)
                if 'relax' in fhead or 'scf' in fhead:
                    os.remove(f.strip())
        
