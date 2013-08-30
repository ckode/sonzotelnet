import time

#=======================================================================
# Looping Call Class
#=======================================================================

class LoopingCall(object):
    """
    Looping Call object.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize looping call.
        """
        self._func = kwargs['func']
        self._looptime = False
        self._runtime = time.time() + self._looptime
        self._args = args

        
    def start(self, looptime):
        """
        Start looping call with loop time interval.
        """

        if type(looptime) is type(1) or type(looptime) is type(.2):
            self._looptime = looptime
            self._runtime = time.time() + self._looptime
        else:
            return False
    

    def execute(self):
        """
        Execute looping call.
        """
        if self._looptime:
            if self._runtime <= time.time():
                self._func(*self._args)
                self._runtime = time.time() + self._looptime
                return  
        return
        
        
#=======================================================================
# CallLater Class
#=======================================================================

class CallLater(object):
    """
    Call Later object.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize calllater class.
        """
        self._func = kwargs['func']
        self.runtime = time.time() + kwargs['runtime']
        self._args = args
        self._kwargs = kwargs
        
    def execute(self):
        """
        Execute callLater.
        """
        result = self._func(*self._args)
        return
        
#=======================================================================
# Installed function Class
#=======================================================================

class InstallFunction(object):
    """
    Installed Function object.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize InstalledFunction class.
        """
        self._func = kwargs['func']
        self._args = args
        self._kwargs = kwargs
        
    def execute(self):
        """
        Execute InstalledFunction.
        """
        self._func(*self._args)
        return