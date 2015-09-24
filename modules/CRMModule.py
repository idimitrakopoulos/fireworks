from lib.Toolkit import log, readPropertyFromPropertiesFile, scriptGlobals
from modules.Module import Module


class CRMModule(Module):

    '''
    classdocs
    '''   
    
    def __init__(self, moduleFilename, modulePropertiesFilename, environmentPropertiesFilename):
        '''
        Constructor
        '''
        self.moduleFilename = moduleFilename
        self.name = readPropertyFromPropertiesFile("name", scriptGlobals.moduleSectionName, modulePropertiesFilename)        
        self.CMSHost = readPropertyFromPropertiesFile("VNACmsHost", self.name, environmentPropertiesFilename)
        self.CMSPort = readPropertyFromPropertiesFile("VNACmsPort", self.name, environmentPropertiesFilename)
        self.CMSUser = readPropertyFromPropertiesFile("VNACmsUser", self.name, environmentPropertiesFilename)
        self.CMSStructureFilename = readPropertyFromPropertiesFile("CMSStructureFilename", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        

        
                
        
        log.info(self.__class__.__name__ + " '" + self.name + "' initialized")