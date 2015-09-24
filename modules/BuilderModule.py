from lib.Toolkit import log, readPropertyFromPropertiesFile, scriptGlobals
from modules.Module import Module


class BuilderModule(Module):

    '''
    classdocs
    '''   
    
    def __init__(self, moduleFilename, modulePropertiesFilename, environmentPropertiesFilename):
        '''
        Constructor
        '''
        self.moduleFilename = moduleFilename
        self.name = readPropertyFromPropertiesFile("name", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        
        self.pluginBinaries = readPropertyFromPropertiesFile("pluginBinaries", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        
        pl=readPropertyFromPropertiesFile("pluginNames", scriptGlobals.moduleSectionName, modulePropertiesFilename) 
        self.pluginList = pl.split(",")
                    
        self.pluginInstalledModulesFolder = readPropertyFromPropertiesFile("pluginInstalledModulesFolder", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        
        self.pluginInstallationFolder = readPropertyFromPropertiesFile("pluginInstallationFolder", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        
        rCF = readPropertyFromPropertiesFile("relativeCleanUpFiles", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        self.relativeCleanUpFiles = rCF.split(",")     
                         
        log.info(self.__class__.__name__ + " '" + self.name + "' initialized")