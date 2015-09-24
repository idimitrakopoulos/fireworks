from lib.Toolkit import log
from postexeclogic.PostExecLogic import PostExecLogic


class GenericPostExecLogic(PostExecLogic):
    '''
    Generic Post-execution logic class
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        PostExecLogic.__init__(self, module)

        ######################################################################
        ##
        ## Developer Note:
        ##
        ## This is a Generic post-execution logic module reserved for potential
        ## future use. If you want to have post-execution logic for your own
        ## product, please create a new file called <PRODUCTNAME>PostExecLogic and
        ## subclass the PostExecLogic class.
        ##
        ## Make sure you call the baseclass constructor as shown below
        ##
        ## PostExecLogic.__init__(self, module)
        ##
        ## (You can take this file as a sample)
        ##
        ######################################################################