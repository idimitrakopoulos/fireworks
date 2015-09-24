from lib.Toolkit import log, readPropertyFromPropertiesFile, scriptGlobals
from modules.Module import Module

class EuclidModule(Module):
    '''
    classdocs
    '''       
    def __init__(self, moduleFilename, modulePropertiesFilename, environmentPropertiesFilename):
        '''
        Constructor
        '''
        self.moduleFilename = moduleFilename
        self.name = readPropertyFromPropertiesFile("name", scriptGlobals.moduleSectionName, modulePropertiesFilename)        
        self.targetDeploymentPath = readPropertyFromPropertiesFile("TARGET_DEPLOYMENT_PATH", self.name, environmentPropertiesFilename)
        self.targetDeploymentProfile = readPropertyFromPropertiesFile("TARGET_DEPLOYMENT_PROFILE", self.name, environmentPropertiesFilename)        
        self.euclidConfigDir = readPropertyFromPropertiesFile("EUCLID_CONFIG_DIR", self.name, environmentPropertiesFilename)
        
        self.relativeMergableConfigurationFiles = readPropertyFromPropertiesFile("relativeMergableConfigurationFiles", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        self.relativeMergableConfigurationFiles = dict(item.split("=") for item in self.relativeMergableConfigurationFiles.split(";") if len(item)>0)
        
        self.relativeWarsToBeExploded = readPropertyFromPropertiesFile("relativeWarsToBeExploded", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        self.relativeWarsToBeExploded = dict(item.split("=") for item in self.relativeWarsToBeExploded.split(";") if len(item)>0)
        
        self.relativeDatabaseUpgrateDescriptionFilePath = readPropertyFromPropertiesFile("relativeDatabaseUpgrateDescriptionFilePath", scriptGlobals.moduleSectionName, modulePropertiesFilename)
         
        log.info(self.__class__.__name__ + " '" + self.name + "' initialized")


class CommonModule(Module):
    '''
    classdocs
    '''       
    def __init__(self, moduleFilename, modulePropertiesFilename, environmentPropertiesFilename):
        '''
        Constructor
        '''
        self.moduleFilename = moduleFilename
        self.name = readPropertyFromPropertiesFile("name", scriptGlobals.moduleSectionName, modulePropertiesFilename)        
        self.targetDeploymentPath = readPropertyFromPropertiesFile("TARGET_DEPLOYMENT_PATH", self.name, environmentPropertiesFilename)
        self.targetDeploymentProfile = readPropertyFromPropertiesFile("TARGET_DEPLOYMENT_PROFILE", self.name, environmentPropertiesFilename)        
        self.euclidConfigDir = readPropertyFromPropertiesFile("EUCLID_CONFIG_DIR", self.name, environmentPropertiesFilename)
        
        self.relativeMergableConfigurationFiles = readPropertyFromPropertiesFile("relativeMergableConfigurationFiles", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        self.relativeMergableConfigurationFiles = dict(item.split("=") for item in self.relativeMergableConfigurationFiles.split(";") if len(item)>0)
        
        self.relativeWarsToBeExploded = readPropertyFromPropertiesFile("relativeWarsToBeExploded", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        self.relativeWarsToBeExploded = dict(item.split("=") for item in self.relativeWarsToBeExploded.split(";") if len(item)>0)
         
        log.info(self.__class__.__name__ + " '" + self.name + "' initialized")
