'''
Created on 30 Ìבס 2011

@author: akalokiris
'''
from modules.Module import Module
from lib.Toolkit import readPropertyFromPropertiesFile, scriptGlobals, log

class MSRuntimeSubModule(Module):
    '''
    classdocs
    '''

    def __init__(self, moduleFileName, modulePropertiesFilename, environmentPropertiesFilename ):
        '''
        Constructor
        '''
    
        self.moduleFilename = moduleFileName
        self.name = readPropertyFromPropertiesFile("name", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        self.relativeWarPath = readPropertyFromPropertiesFile("relativeWarPath", scriptGlobals.moduleSectionName, modulePropertiesFilename)
#        self.absolutCopyableFilesOrFolders = readPropertyFromPropertiesFile("absolutCopyableFilesOrFolders", scriptGlobals.moduleSectionName, modulePropertiesFilename)
#        self.absolutCopyableFilesOrFolders = dict(item.split("=") for item in self.absolutCopyableFilesOrFolders.split(";"))
     
        log.info(self.__class__.__name__ + " '" + self.name + "' initialized")