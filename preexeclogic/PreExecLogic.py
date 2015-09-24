import getpass
from lib.Toolkit import log, checkPythonVersion, scriptGlobals, checkRequiredExecutablesExist, changePathPermissions, getPathPermissions, die, checkUserIsRoot
import lib.OptParser

class PreExecLogic:
    '''
    Pre-execution logic for Fireworks.

    This is the mandatory pre-execution logic that needs to run on every Fireworks execution.

    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        log.debug(self.__class__.__name__ + " initialized")
        
        # Check if the current python version is correct
        checkPythonVersion(scriptGlobals.pythonMajorVersion, scriptGlobals.pythonMinorVersion)

        # Check for required executables
        checkRequiredExecutablesExist(scriptGlobals.requiredExecutables)

        # Check user isn't root
        if checkUserIsRoot(getpass.getuser()):
            die("User is '" + getpass.getuser() + "'. The script shouldn't run with superuser permissions.")

        # Check action validity according to current module
        if (not lib.OptParser.options.action in module.actionBundleGroupClasses):
            die("Unrecognized action '" + lib.OptParser.options.action + "'")

        # Make Oracle tool executable
        if getPathPermissions(scriptGlobals.sqlplusLocation) != 0755 :
            log.debug("SQLPlus file" + scriptGlobals.sqlplusLocation + " isn't executable. Changing its permissions to executable.")
            changePathPermissions(scriptGlobals.sqlplusLocation, 0755)


