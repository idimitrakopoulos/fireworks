from lib.Toolkit import log
from preexeclogic.PreExecLogic import PreExecLogic


class GenericPreExecLogic(PreExecLogic):
    '''
    Generic Pre-execution logic class
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        PreExecLogic.__init__(self, module)

        ######################################################################
        ##
        ## Developer Note:
        ##
        ## This is a Generic pre-execution logic module reserved for potential
        ## future use. If you want to have pre-execution logic for your own
        ## product, please create a new file called <PRODUCTNAME>PreExecLogic and
        ## subclass the PreExecLogic class.
        ##
        ## Make sure you call the baseclass constructor as shown below
        ##
        ## PreExecLogic.__init__(self, module)
        ##
        ## (You can take this file as a sample)
        ##
        ######################################################################