'''
Created on 30 Ìבס 2011

@author: akalokiris
'''
from actionbundles.ActionBundle import ActionBundle
from lib.Toolkit import generateGUID, log, getProcessPIDByPath, die, \
    createDirectoriesRecursively, scriptGlobals, sprintfOnDictionaryValues,\
    grepFile
from actions.FileSystemActions import ExtractZipToDir, CopyDirOrFile,\
    CopyDirOrFile2, ExtractFileFromZipToDir
import lib.OptParser
from actions.ConfigurationActions import ConfigureTemplateFile,\
    CheckFileConfigurationIsComplete



class MSRuntimeCleanInitAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)
  
        # Check if JBOSS is running
        if getProcessPIDByPath(module.targetDeploymentPath):die("The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")    
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()    
        log.info("Unique ActionBundle execution ID generated: " + guid)    
        
        # Prepare directory to unpack package
        module.subModule.unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")
        
        # Extract MS Runtime package into tmp dir
        ExtractZipToDir(module.moduleFilename, module.subModule.unzippedPackagePath)    

        # Extract MANIFEST.MF
        ExtractFileFromZipToDir(module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeWarPath, module.relativeVersionInformationPath, module.subModule.unzippedPackagePath)    

        # Since MS is deployed on JBOSS some paths have an %s to allow a configurable 
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)
        # end    

class MSRuntimeUpdateInitAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)
        
        # Check if JBOSS is running
        if getProcessPIDByPath(module.targetDeploymentPath):die("The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")    
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()    
        log.info("Unique ActionBundle execution ID generated: " + guid)    

        # Prepare directory to unpack package
        module.subModule.unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")
        
        # Extract MS Runtime package into tmp dir
        ExtractZipToDir(module.moduleFilename, module.subModule.unzippedPackagePath)    

        # Prepare directory to unpack package
        module.subModule.previousVersionBackupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "previousVersionBackup")        

        # Extract new MANIFEST.MF
        ExtractFileFromZipToDir(module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeWarPath, module.relativeVersionInformationPath, module.subModule.unzippedPackagePath)    

        # Prepare directory to keep backups
        # Since MS is deployed on JBOSS some paths have an %s to allow a configurable 
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)
        # end

class MSRuntimeDeployWarAB(ActionBundle):
    '''
    classdocs
    '''


    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()    
        log.info("Unique ActionBundle execution ID generated: " + guid)
        
        # Copy marketing-suite-runtime.war to deploy
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactExtractedLocation = module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)        
        # end 
        
class MSRuntimeDeployConfAB(ActionBundle):
    '''
    classdocs
    '''


    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()    
        log.info("Unique ActionBundle execution ID generated: " + guid)                
 
        # Configure marketing-suite-runtime.properties using envprops
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)

        # Copy marketing-suite-runtime.properties to conf
        # Copy jboss-log4j.xml to conf
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)    
        # end        
        
class MSRuntimeBackUpAB(ActionBundle):
    '''
    classdocs
    '''


    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()    
        log.info("Unique ActionBundle execution ID generated: " + guid)        
        
        previousVersionBackupPath = module.subModule.previousVersionBackupPath 
        unzippedPackagePath = module.subModule.unzippedPackagePath

        # Backup marketing-runtime-webapp.war from deploy/
        # Backup esb.jar from deploy/
        # Backup ROOT.WAR/crossdmain.xml from deploy/ROOT.WAR
        log.info("######################## COPY ALL COPYABLE FILES ########################")        
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            exactBackupLocation = module.subModule.previousVersionBackupPath + scriptGlobals.osDirSeparator + k
            CopyDirOrFile2(exactLocation, exactBackupLocation)        

             
        # Backup marketing-suite-runtime-deployment.properties from conf
        # Backup jboss-log4j.xml from conf
        # Backup web.xml from marketing-runtime-webapp.war/WEB-INF        
        log.info("######################## COPY ALL COPYABLE FILES ########################")        
        for k, v in module.relativeConfigurationFiles.items():
            exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            exactBackupLocation = previousVersionBackupPath + scriptGlobals.osDirSeparator + k
            CopyDirOrFile2(exactLocation, exactBackupLocation)        

      
        log.info("######################## END OF COPY ########################")        
        # Extract old MANIFEST.MF
        ExtractFileFromZipToDir(previousVersionBackupPath + scriptGlobals.osDirSeparator+module.subModule.relativeWarPath, module.relativeVersionInformationPath, previousVersionBackupPath)    

        # Compare current and new versions
        log.info("Version currently installed    : " + grepFile(module.versionInformationRegex, previousVersionBackupPath + scriptGlobals.osDirSeparator + "MANIFEST.MF"))
        log.info("Revision currently installed   : " + grepFile(module.revisionInformationRegex, previousVersionBackupPath + scriptGlobals.osDirSeparator + "MANIFEST.MF"))
        log.info("Version to be installed        : " + grepFile(module.versionInformationRegex, unzippedPackagePath + scriptGlobals.osDirSeparator + "MANIFEST.MF"))        
        log.info("Revision to be installed       : " + grepFile(module.revisionInformationRegex, unzippedPackagePath + scriptGlobals.osDirSeparator + "MANIFEST.MF"))        
        #end    