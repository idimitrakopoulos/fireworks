'''
Created on 30 ��� 2011

@author: akalokiris
'''
from actionbundles.ActionBundle import ActionBundle
from lib.Toolkit import generateGUID, log, getProcessPIDByPath, die, \
    createDirectoriesRecursively, scriptGlobals, sprintfOnDictionaryValues,\
    readPropertyFromPropertiesFile, grepFile
from actions.FileSystemActions import ExtractZipToDir, CopyDirOrFile,\
    CopyDirOrFile2, ExtractFileFromZipToDir, ExecuteOSCommand, DeleteDirOrFile
import lib.OptParser
from actions.ConfigurationActions import ConfigureTemplateFile,\
    CheckFileConfigurationIsComplete
import os
from src.actions.FileSystemActions import DeleteDirOrFile



class MSRouterCleanInitAB(ActionBundle):
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

        # Extract MS Router package into tmp dir
        ExtractZipToDir(module.moduleFilename, module.subModule.unzippedPackagePath)

        # Extract MANIFEST.MF
        ExtractFileFromZipToDir(module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeWarPath, module.relativeVersionInformationPath, module.subModule.unzippedPackagePath)

        # Since MS is deployed on JBOSS some paths have an %s to allow a configurable
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)
        # end

class MSRouterUpdateInitAB(ActionBundle):
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

        # Extract MS Router package into tmp dir
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

class MSRouterDeployWarAB(ActionBundle):
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

        # Copy marketing-suite-router.war to deploy
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactExtractedLocation = module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)
        # end

class MSRouterDeployConfAB(ActionBundle):
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

        # Configure marketing-suite-router.properties using envprops
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)

        # Copy marketing-suite-router.properties to conf
        # Copy jboss-log4j.xml to conf
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)
        # end

class MSRouterBackUpAB(ActionBundle):
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

        # Backup marketing-router-webapp.war from deploy/
        # Backup esb.jar from deploy/
        # Backup ROOT.WAR/crossdmain.xml from deploy/ROOT.WAR
        log.info("######################## COPY ALL COPYABLE FILES ########################")
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            exactBackupLocation = module.subModule.previousVersionBackupPath + scriptGlobals.osDirSeparator + k
            CopyDirOrFile2(exactLocation, exactBackupLocation)


        # Backup marketing-suite-router-deployment.properties from conf
        # Backup jboss-log4j.xml from conf
        # Backup web.xml from marketing-router-webapp.war/WEB-INF
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


class MSRouterRunJarAB(ActionBundle):
    '''
    classdocs
    '''


    def __init__(self, module):
        '''
        Constructor
        '''

        ActionBundle.__init__(self, module)

        unzippedPackagePath = module.subModule.unzippedPackagePath
        propertiesFileName = "upgrade-configuration.properties"

        # Run migration jars
        ls = os.listdir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeJarFilesPath)
        ls.sort()

        for zipFile in ls:
            # Extract MS Router package into tmp dir
            ExtractZipToDir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeJarFilesPath + scriptGlobals.osDirSeparator + zipFile, unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeJarFilesPath)

            #Get jar name from zip name
            jarFile = zipFile[:-4] + ".jar"

            # extract properties to current dir
            ExtractFileFromZipToDir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeJarFilesPath + scriptGlobals.osDirSeparator + jarFile, propertiesFileName, ".")

            # configure properties
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, propertiesFileName)
            CheckFileConfigurationIsComplete(propertiesFileName)

            # add configured properties to zip
            ExecuteOSCommand("zip -r "+ unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeJarFilesPath + scriptGlobals.osDirSeparator + jarFile + " " + propertiesFileName, '')

            # delete properties from current dir
            DeleteDirOrFile(propertiesFileName);

            # run migration jar
            jarCommand = "java -jar " + unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeJarFilesPath + scriptGlobals.osDirSeparator + jarFile
            log.info("Jar file " + jarFile + "will be executed with the following command \n" + jarCommand)
            ExecuteOSCommand(jarCommand, '')

        #end

