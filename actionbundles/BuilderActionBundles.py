from actionbundles.ActionBundle import ActionBundle
from lib.Toolkit import log, scriptGlobals, getProcessPIDByPath, die, generateGUID, createDirectoriesRecursively, sprintfOnDictionaryValues, sprintfOnListValues, readPropertyFromPropertiesFile
from actions.FileSystemActions import CopyDirOrFile, ExtractZipToDir, CreateDirectoriesRecursively, DeleteDirOrFile, MoveDirOrFile
from actions.ConfigurationActions import ConfigureTemplateFile, CheckFileConfigurationIsComplete
import lib.OptParser
import glob
import os
import shutil


class BuilderCleanAB(ActionBundle):
    '''
    Perform a clean Builder installation
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)
        
        # Check if JBOSS is running
        if getProcessPIDByPath(module.targetDeploymentPath): die("The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")        
        
        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")
        
        # Since Builder is deployed on JBOSS some paths have an %s to allow a configurable 
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile) 
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)                
        sprintfOnListValues(module.subModule.relativeCleanUpFiles, module.targetDeploymentProfile)
        
        
        # Extract Builder package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)
        
        # Configure m-web-builder.properties using envprops
        # Configure mgage.properties using envprops
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)
       
        
        # Copy m-web-builder.properties to conf
        # Copy mgage.properties to conf
        # Copy jboss-log4j.xml to conf
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)       


         # Clean up files that might have been left over from previous manuall installations
        cleanUp(module)
        
        # Copy artifacts to profile
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)
            
        # Create custom templates & static folder        
        customTemplatesFolder = readPropertyFromPropertiesFile("CUSTOM_TEMPLATES_FOLDER", module.name, lib.OptParser.options.envprops)
        CreateDirectoriesRecursively(customTemplatesFolder)
        
        # Create cmsExports folder
        staticFolder = readPropertyFromPropertiesFile("STATIC_FOLDER", module.name, lib.OptParser.options.envprops)
        cmsExportsFolder = staticFolder + scriptGlobals.osDirSeparator + "cmsExports"        
        CreateDirectoriesRecursively(cmsExportsFolder)
        
        # Create uploads folder -- apparently CMS needs it
        uploadsFolder = staticFolder + scriptGlobals.osDirSeparator + "uploads"
        CreateDirectoriesRecursively(uploadsFolder)
     
        # Install Plugins      
        installDefaultPlugins(staticFolder, unzippedPackagePath, module)
        
        
        # Find version/revision info
        #versionInfo = grepFile(module.versionInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        #revisionInfo = grepFile(module.revisionInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        
        #versionInfo = (versionInfo.replace(module.versionInformationRegex, "")).strip()
        #revisionInfo = (revisionInfo.replace(module.revisionInformationRegex, "")).strip()            

class BuilderUpdateAB(ActionBundle):
    '''
    Perform a Builder update
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)
        
        # Check if JBOSS is running
        if getProcessPIDByPath(module.targetDeploymentPath): die("The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")        
        
        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")
        
        # Since Builder is deployed on JBOSS some paths have an %s to allow a configurable 
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile) 
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)
        sprintfOnListValues(module.subModule.relativeCleanUpFiles, module.targetDeploymentProfile)
        
        # Extract Builder package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)
        
    
        # Do this again in case new settings have been added
        # Configure m-web-builder.properties using envprops
        # Configure mgage.properties using envprops
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)
        
        
        # Copy m-web-builder.properties to conf
        # Copy mgage.properties to conf
        # Copy jboss-log4j.xml to conf
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)       

        # Clean up files that might have been left over from previous manuall installations
        cleanUp(module)
        
        # Copy artifacts to profile
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)
                
        # Install Plugins    
        staticFolder = readPropertyFromPropertiesFile("STATIC_FOLDER", module.name, lib.OptParser.options.envprops)  
        installDefaultPlugins(staticFolder, unzippedPackagePath, module)
             
      
class BuilderInfoAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        
def markPluginForRemoval(plugin):
    if glob.glob(plugin):
        for name in glob.glob(plugin):
            MoveDirOrFile(name, name + ".remove")
    else:
        log.info("Path does not exist: " + plugin)

def copyPlugins(src, dst):
    for plugin in os.listdir(src):        
        CopyDirOrFile(os.path.join(src, plugin), dst)
            

def installDefaultPlugins(staticFolder, unzippedPackagePath, module):
    # create InstalledModules folder
    pluginInstalledModules = staticFolder + scriptGlobals.osDirSeparator + module.subModule.pluginInstalledModulesFolder
    if not (os.access(pluginInstalledModules, os.F_OK)):
        log.debug("Creating plugin installed modules folder: " + pluginInstalledModules)
        CreateDirectoriesRecursively(pluginInstalledModules)
        
    # create Plugin_Installation folder    
    pluginInstallationFolder = staticFolder + scriptGlobals.osDirSeparator + module.subModule.pluginInstallationFolder
    if not (os.access(pluginInstallationFolder, os.F_OK)):
        log.debug("Creating plugin installation folder: " + pluginInstallationFolder)
        CreateDirectoriesRecursively(pluginInstallationFolder)
           
    # remove any existing default plugins
    for pluginName in module.subModule.pluginList:
        pluginName = pluginName + "*"
        log.debug("Uninstalling " + pluginName + "...")        
        pluginPath = pluginInstallationFolder + scriptGlobals.osDirSeparator + pluginName
        markPluginForRemoval(pluginPath)
        
    # install plugins    
    pluginBinariesFolder = unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.pluginBinaries
    log.debug("Installing default plugins from " + pluginBinariesFolder + " to " + pluginInstallationFolder + "...")
    copyPlugins(pluginBinariesFolder, pluginInstallationFolder)
    

def cleanUp(module): 
    for fileToCleanup in module.subModule.relativeCleanUpFiles:        
        fileToCleanup = module.targetDeploymentPath + scriptGlobals.osDirSeparator + fileToCleanup    
        deleteFile(fileToCleanup)
    
def deleteFile(fileName):
    log.info("Attempting to remove " + fileName + "...")
    if glob.glob(fileName):        
        for name in glob.glob(fileName):
            log.debug("Removing " + name + "...")
            DeleteDirOrFile(name)
    else:
        log.info("Path does not exist: " + fileName)
             
