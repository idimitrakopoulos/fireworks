from lib.Toolkit import log, getAnswerFromUser, scriptGlobals
from random import randint
import re
import lib.OptParser

class Action:
    '''
    A single action
    '''

    def __init__(self):       
        '''
        Appends this Action to Rollback queue
        '''

        # If script runs in attended mode then ask
        if not lib.OptParser.options.unattended:
            a = getAnswerFromUser("Action '" + self.__class__.__name__ + "' " + str(self.__dict__) + " is ready to execute.\n\n Action Documentation:\n" + self.__doc__ +"\n\nSelect your action:\n\n(U) Execute action and continue unattended \n(X) Don't execute current action \n(<any other key>) Execute current action")
            if (re.compile('^u$', re.I)).match(a): lib.OptParser.options.unattended = True
            if (re.compile('^x$', re.I)).match(a):
                log.warn("Skipping current action '" + self.__class__.__name__ + "' " + str(self.__dict__) + "'")
                return
        
        # Run subclass __call__ function
        self()
        
        # Append this action to rollback queue
        log.debug("Appending action '" + self.__class__.__name__ + "' " + str(self.__dict__) + " to rollback queue" )
        scriptGlobals.executedActionList.append(self)


    def removeActionFromRollbackQueue(self):
        log.debug("Removing action '" + self.__class__.__name__ + "' " + str(self.__dict__) + " from rollback queue" )
        scriptGlobals.executedActionList.remove(self)
    
    def generateActionID(self):
        self.actionID = randint(1, 9999999)
        
    def undoSuper(self):
        # If script runs in attended mode then ask
        if not lib.OptParser.options.unattended:                         
            a = getAnswerFromUser("Action '" + self.__class__.__name__ + "' " + str(self.__dict__) + " is ready to execute a rollback action.\n\n Action Documentation:\n" + self.__doc__ +" \n\nSelect your action:\n\n(U) Execute action and continue unattended rollback \n(X) Don't execute current rollback action \n(<any other key>) Execute current action rollback")
            if (re.compile('^u$', re.I)).match(a): lib.OptParser.options.unattended = True
            if (re.compile('^x$', re.I)).match(a):
                log.warn("Skipping the rollback operation of this action '" + self.__class__.__name__ + "' " + str(self.__dict__) + "'")
                return
            
        # Run subclass undo function            
        self.undo()  
       
