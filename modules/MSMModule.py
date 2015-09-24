from lib.Toolkit import log, readPropertyFromPropertiesFile, scriptGlobals
from modules.Module import Module


class MSMModule(Module):

    '''
    classdocs
    '''   
    
    def __init__(self, moduleFilename, modulePropertiesFilename, environmentPropertiesFilename):
        '''
        Constructor
        '''
        self.moduleFilename = moduleFilename
        self.name = readPropertyFromPropertiesFile("subModuleName", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        self.launchType = readPropertyFromPropertiesFile("launchType", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        self.processIdentifier = readPropertyFromPropertiesFile("processIdentifier",  scriptGlobals.moduleSectionName, modulePropertiesFilename)
        self.installUpdateScript = readPropertyFromPropertiesFile("installUpdateScript",  scriptGlobals.moduleSectionName, modulePropertiesFilename)
        Module.buildInformationRegex = readPropertyFromPropertiesFile("buildInformationRegex", scriptGlobals.moduleSectionName, modulePropertiesFilename)

        log.info(self.__class__.__name__ + " '" + self.name + "' initialized")