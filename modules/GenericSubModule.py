from lib.Toolkit import log, readPropertyFromPropertiesFile, scriptGlobals
from modules.Module import Module


class GenericSubModule(Module):

    '''
    classdocs
    '''   
    
    def __init__(self, moduleFilename, modulePropertiesFilename, environmentPropertiesFilename):
        '''
        Constructor
        '''
        self.moduleFilename = moduleFilename
        self.name = readPropertyFromPropertiesFile("name", scriptGlobals.moduleSectionName, modulePropertiesFilename)        
                
        
        log.info(self.__class__.__name__ + " '" + self.name + "' initialized")