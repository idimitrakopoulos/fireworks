'''
Created on 30 ��� 2011

@author: akalokiris
'''
from modules.Module import Module
from lib.Toolkit import readPropertyFromPropertiesFile, scriptGlobals, log

class MSRuntimeRouterSubModule(Module):
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
        self.relativeJarFilesPath = readPropertyFromPropertiesFile("relativeJarFilesPath", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        log.info(self.__class__.__name__ + " '" + self.name + "' initialized")
