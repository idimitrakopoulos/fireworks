from lib.Toolkit import log


class PostExecLogic:
    '''
    Post-execution logic for Fireworks.

    This is the mandatory post-execution logic that needs to run on every Fireworks execution.

    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        log.debug(self.__class__.__name__ + " initialized")
