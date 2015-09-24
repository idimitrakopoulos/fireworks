from actionbundles.ActionBundle import ActionBundle
from lib.Toolkit import log, scriptGlobals, getProcessPIDByPath, die, generateGUID, createDirectoriesRecursively 
from lib.Toolkit import sprintfOnDictionaryValues, readPropertyFromPropertiesFile, replaceInsensitiveStringInFile 
from lib.Toolkit import extractFileFromZipToDir, grepFile, getAnswerFromUser, moveDirOrFile
from actions.FileSystemActions import CopyDirOrFile, ExtractZipToDir, CreateDirectory, DeleteDirOrFile, MoveDirOrFile
from actions.ConfigurationActions import ConfigureTemplateFile, CheckFileConfigurationIsComplete
from actions.DatabaseActions import RunOracleScriptFromFile
import lib.OptParser
from actions.Action import Action
from modules.AnalyticsModules import EuclidModule
import ConfigParser
import os
from string import rfind
import re
import string

class CommonInstallAB(ActionBundle):
    '''
    Clean & Update installation
    '''
    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)
        commonModule = module.subModule
        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)
        # Check if JBOSS is running
        if getProcessPIDByPath(module.targetDeploymentPath): die("The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")        
        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")
        # Prepare backup directory
        backupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "backup")
        # Prepare explode wars directory
        explodePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "explode")
        # Prepare configuration directory
        configDirectoryPath = createDirectoriesRecursively(commonModule.euclidConfigDir)
        # Since Euclid is deployed on JBOSS some paths have an %s to allow a configurable 
        # config dir, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile) 
        sprintfOnDictionaryValues(commonModule.relativeMergableConfigurationFiles, commonModule.euclidConfigDir)
        # Since Euclid is deployed on JBOSS some paths have an %s to allow a configurable 
        # server profile, so do a little sprintf to fix them   
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile) 
        sprintfOnDictionaryValues(commonModule.relativeWarsToBeExploded, module.targetDeploymentProfile)
        # Extract package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)
        # Configure relativeConfigurationFiles
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)
        # Configure relativeMergableConfigurationFiles
        for k, v in commonModule.relativeMergableConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)
        # Explode wars
        for k, v in commonModule.relativeWarsToBeExploded.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            i = rfind(k, scriptGlobals.osDirSeparator)
            if i > -1: 
                tmpExplodeWarLocation = explodePath + scriptGlobals.osDirSeparator + k[i+1:]
            else:
                tmpExplodeWarLocation = explodePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            backupFileOrDirIfExists(exactTargetLocation,backupPath)
            createDirectoriesRecursively(tmpExplodeWarLocation)
            ExtractZipToDir(exactExtractedLocation, tmpExplodeWarLocation)
            AltMoveDirOrFile(tmpExplodeWarLocation,exactTargetLocation)
        # Copy config files
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            backupFileOrDirIfExists(exactTargetLocation,backupPath)
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation) 
        # Copy mergable config files (no need to merge on clean install)
        for k, v in commonModule.relativeMergableConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = v 
            backupFileOrDirIfExists(exactTargetLocation,backupPath)
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)       
        # Copy other files
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            backupFileOrDirIfExists(exactTargetLocation,backupPath)
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)


class EuclidCleanAB(ActionBundle):
    '''
    Clean Euclid installation
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)
        euclidModule = module.subModule
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)
        
        # Check if JBOSS is running
        if getProcessPIDByPath(module.targetDeploymentPath): die("The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")        
        
        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")
        
        # Prepare backup directory
        backupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "backup")
        
        # Prepare explode wars directory
        explodePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "explode")        
        
        # Prepare configuration directory
        configDirectoryPath = createDirectoriesRecursively(euclidModule.euclidConfigDir)
        
        # Since Euclid is deployed on JBOSS some paths have an %s to allow a configurable 
        # config dir, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile) 
        sprintfOnDictionaryValues(euclidModule.relativeMergableConfigurationFiles, euclidModule.euclidConfigDir)
        # Since Euclid is deployed on JBOSS some paths have an %s to allow a configurable 
        # server profile, so do a little sprintf to fix them   
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile) 
        sprintfOnDictionaryValues(euclidModule.relativeWarsToBeExploded, module.targetDeploymentProfile)

        # Extract package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)
        
        # Configure relativeConfigurationFiles
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
            replaceInsensitiveStringInFile("${CREATE_SCHEMA}", "true", exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)
        
        # Configure relativeMergableConfigurationFiles
        for k, v in euclidModule.relativeMergableConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
            replaceInsensitiveStringInFile("${CREATE_SCHEMA}", "true", exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)
        
        # Explode wars
#        for k, v in euclidModule.relativeWarsToBeExploded.items():
#            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
#            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
#            backupFileOrDirIfExists(exactTargetLocation,backupPath)
#            ExtractZipToDir(exactExtractedLocation, exactTargetLocation)
        for k, v in euclidModule.relativeWarsToBeExploded.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            i = rfind(k, scriptGlobals.osDirSeparator)
            if i > -1: 
                tmpExplodeWarLocation = explodePath + scriptGlobals.osDirSeparator + k[i+1:]
            else:
                tmpExplodeWarLocation = explodePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            backupFileOrDirIfExists(exactTargetLocation,backupPath)
            createDirectoriesRecursively(tmpExplodeWarLocation)
            ExtractZipToDir(exactExtractedLocation, tmpExplodeWarLocation)
            AltMoveDirOrFile(tmpExplodeWarLocation,exactTargetLocation)
            
        # Copy config files
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            backupFileOrDirIfExists(exactTargetLocation,backupPath)
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation) 
        # Copy mergable config files (no need to merge on clean install)
        for k, v in euclidModule.relativeMergableConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = v 
            backupFileOrDirIfExists(exactTargetLocation,backupPath)
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)       
        # Copy other files
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            backupFileOrDirIfExists(exactTargetLocation,backupPath)
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)


class EuclidUpdateAB(ActionBundle):
    '''
    Update Euclid installation
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)
        euclidModule = module.subModule
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)
        
        # Check if JBOSS is running
        if getProcessPIDByPath(module.targetDeploymentPath): die("The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")        
        
        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")
        
        # Prepare backup directory
        backupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "backup")
        
        # Prepare explode wars directory
        explodePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "explode")
        
        # Prepare configuration directory
        configDirectoryPath = createDirectoriesRecursively(euclidModule.euclidConfigDir)
        
        # Since Euclid is deployed on JBOSS some paths have an %s to allow a configurable 
        # config dir, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile) 
        sprintfOnDictionaryValues(euclidModule.relativeMergableConfigurationFiles, euclidModule.euclidConfigDir)
        # Since Euclid is deployed on JBOSS some paths have an %s to allow a configurable 
        # server profile, so do a little sprintf to fix them   
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile) 
        sprintfOnDictionaryValues(euclidModule.relativeWarsToBeExploded, module.targetDeploymentProfile)

        # Extract package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)
        
        versionTmpPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "tmp")
        installedWarPath = module.targetDeploymentPath + scriptGlobals.osDirSeparator + "server" + scriptGlobals.osDirSeparator + module.targetDeploymentProfile + scriptGlobals.osDirSeparator + "deploy" + scriptGlobals.osDirSeparator + module.name + ".war"
        installedVersionInfo = getVersionInfoFromWar(installedWarPath, module.relativeVersionInformationPath, module.versionInformationRegex, module.revisionInformationRegex, versionTmpPath)
        newWarPath = unzippedPackagePath + scriptGlobals.osDirSeparator + "bin" + scriptGlobals.osDirSeparator + module.name + ".war"
        newVersionInfo = getVersionInfoFromWar(newWarPath, module.relativeVersionInformationPath, module.versionInformationRegex, module.revisionInformationRegex, versionTmpPath)
        log.info("\n------ UPDATE VERSION INFO ------------------------" + 
                 "\nCurrently installed: " + installedVersionInfo[0] + " (" + installedVersionInfo[1] + ")" + 
                 "\n    To be installed: " + newVersionInfo[0] + " (" + newVersionInfo[1] + ")" +
                 "\n---------------------------------------------------")
        versionSameOrNewer=False
        if compareVersions(newVersionInfo[0], installedVersionInfo[0]) < 0 :
            versionSameOrNewer=True
            continueOrCancel("\nWARNING: Installed version is newer! If you continue the installation DB migration will not be executed.")
        elif compareVersions(newVersionInfo[0], installedVersionInfo[0]) == 0 :
            versionSameOrNewer=True
            continueOrCancel("\nWARNING: Same version already installed! If you continue the installation DB migration will not be executed.")
        
        # Configure relativeConfigurationFiles
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
            replaceInsensitiveStringInFile("${CREATE_SCHEMA}", "false", exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)
        
        # Configure relativeMergableConfigurationFiles
        for k, v in euclidModule.relativeMergableConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
            replaceInsensitiveStringInFile("${CREATE_SCHEMA}", "false", exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)
        
        # Explode wars
#        for k, v in euclidModule.relativeWarsToBeExploded.items():
#            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
#            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
#            backupFileOrDirIfExists(exactTargetLocation,backupPath)
#            ExtractZipToDir(exactExtractedLocation, exactTargetLocation)
        for k, v in euclidModule.relativeWarsToBeExploded.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            i = rfind(k, scriptGlobals.osDirSeparator)
            if i > -1: 
                tmpExplodeWarLocation = explodePath + scriptGlobals.osDirSeparator + k[i+1:]
            else:
                tmpExplodeWarLocation = explodePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            backupFileOrDirIfExists(exactTargetLocation,backupPath)
            createDirectoriesRecursively(tmpExplodeWarLocation)
            ExtractZipToDir(exactExtractedLocation, tmpExplodeWarLocation)
            AltMoveDirOrFile(tmpExplodeWarLocation,exactTargetLocation)
        
        # Copy config files
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            backupFileOrDirIfExists(exactTargetLocation,backupPath)
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation) 
            
        # Copy merge config files and copy (just copy for now)
        for k, v in euclidModule.relativeMergableConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = v 
            backupFileOrDirIfExists(exactTargetLocation,backupPath)
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)
#            secondaryFileName = unzippedPackagePath + scriptGlobals.osDirSeparator + k
#            mergedFileName = secondaryFileName+".merged"
#            primaryFileName = v 
#            MergeSectionlessConfigFiles(primaryFileName, secondaryFileName, mergedFileName)
#            CopyDirOrFile(mergedFileName, primaryFileName)      

        # Copy other files
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            backupFileOrDirIfExists(exactTargetLocation,backupPath)
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)
        
        #Construct DB connection string
        if versionSameOrNewer:
            log.info("Skipping DB migration scripts execution!")
            return
        dbUsername = readPropertyFromPropertiesFile("DB_CONNECTION_USERNAME", module.name, lib.OptParser.options.envprops)
        dbPassword = readPropertyFromPropertiesFile("DB_CONNECTION_PASSWORD", module.name, lib.OptParser.options.envprops)
        connUrl = readPropertyFromPropertiesFile("DB_CONNECTION_URL", module.name, lib.OptParser.options.envprops)
        finalConnectionString = string.replace(connUrl, '@', dbUsername + '/' + dbPassword + '@', 1)
        
        # Execute DB migration scripts
        confParser = ConfigParser.ConfigParser()
        confParser.read(unzippedPackagePath + scriptGlobals.osDirSeparator + euclidModule.relativeDatabaseUpgrateDescriptionFilePath)
        ok, scripts, default = getDbUpdateScriptsToRun(installedVersionInfo[0], confParser)
        if ok == False:
            continueOrCancel("\nERROR: This installer does not support updating from " + installedVersionInfo[0] + " version!")
        elif len(default)>0:
            log.info('DB update scripts to be executed:\n' + string.join(scripts, ", "))
            continueOrCancel("\nWARNING: Default DB update scripts are used for branch(es) " + string.join(default,", ") + ". This is probably probably OK, but you should make sure that the currently installed version is supported by the update procedure (please read the deployment instructions or consult with the development team).")
        else:
            log.info('DB update scripts to be executed:\n' + string.join(scripts, ", "))
        baseDbScriptPath = unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + scriptGlobals.osDirSeparator
        for script in scripts:
            #print "Execute: " + baseDbScriptPath + script
            RunOracleScriptFromFile(baseDbScriptPath + script, finalConnectionString)


class CommonInfoAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)
        euclidModule = module.subModule
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)
        versionTmpPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "tmp")
        installedWarPath = module.targetDeploymentPath + scriptGlobals.osDirSeparator + "server" + scriptGlobals.osDirSeparator + module.targetDeploymentProfile + scriptGlobals.osDirSeparator + "deploy" + scriptGlobals.osDirSeparator + module.name + ".war"
        installedVersionInfo = getVersionInfoFromWar(installedWarPath, module.relativeVersionInformationPath, module.versionInformationRegex, module.revisionInformationRegex, versionTmpPath)
        newWarPath = unzippedPackagePath + scriptGlobals.osDirSeparator + "bin" + scriptGlobals.osDirSeparator + module.name + ".war"
        newVersionInfo = getVersionInfoFromWar(newWarPath, module.relativeVersionInformationPath, module.versionInformationRegex, module.revisionInformationRegex, versionTmpPath)
        print "\n------ UPDATE VERSION INFO ------"
        print "Currently installed: " + installedVersionInfo[0] + " (" + installedVersionInfo[1] + ")"
        print "    To be installed: " + newVersionInfo[0] + " (" + newVersionInfo[1] + ")\n"


class AltMoveDirOrFile(Action):
    '''
    DO: Move a directory or a file
    UNDO: Move back a directory or a file    
    '''
    def __init__(self, src, dst): 
        log.debug(self.__class__.__name__ + " initialized")
        self.src = src
        self.dst = dst
        self.srcDirname = os.path.dirname(src)
        self.dstDirname = os.path.dirname(dst)
        self.srcBasename = os.path.basename(src)
        self.dstBasename = os.path.basename(dst)
        self.isSrcDir = os.path.isdir(src)
        self.isDstDir = os.path.isdir(dst)
        self.isSrcExistent = os.path.exists(src)
        self.isDstExistent = os.path.exists(dst)
        Action.__init__(self)        
                
    def __call__(self):
        moveDirOrFile(self.srcDirname + scriptGlobals.osDirSeparator + self.srcBasename,
                      self.dstDirname + scriptGlobals.osDirSeparator + self.dstBasename)

    def undo(self):
        if self.isDstDir : #dst was an existent directory
            _from = self.dstDirname + scriptGlobals.osDirSeparator + self.dstBasename + scriptGlobals.osDirSeparator + self.srcBasename
            _to = self.srcDirname + scriptGlobals.osDirSeparator + self.srcBasename
        elif not self.isDstExistent: #dst did not exist
            _from = self.dstDirname + scriptGlobals.osDirSeparator + self.dstBasename
            _to = self.srcDirname + scriptGlobals.osDirSeparator + self.srcBasename
        elif self.isDstExistent and not self.isSrcDir: #both dst and src were files
            _from = self.dstDirname + scriptGlobals.osDirSeparator + self.dstBasename
            _to = self.srcDirname + scriptGlobals.osDirSeparator ++ self.srcBasename
        else: #src was a directory and dst was probably a file -> an exception should have been raised!
            pass
        moveDirOrFile(_from, _to)
    
    def report(self):
        log.info("mv " + self.src + " " + self.dst)


def backupFileOrDirIfExists(location,backupPath):
    if os.path.isfile(location) or os.path.isdir(location):
        if len(location)==0:
            return
        if location[len(location)-1]==scriptGlobals.osDirSeparator:
            location=location[:-1]
        i = rfind(location, scriptGlobals.osDirSeparator)
        if i > -1: 
            backupLocation = backupPath+scriptGlobals.osDirSeparator+location[i+1:]
        else:
            backupLocation = backupPath+scriptGlobals.osDirSeparator+location
        log.info('Backing-up "'+location+'" to "'+backupLocation+'"')
        AltMoveDirOrFile(location,backupLocation)


def getVersionInfoFromWar(warPath, relativeVersionInformationPath, versionInformationRegex, revisionInformationRegex, tmpPath):
    if os.path.isfile(warPath):
        #This is a war file
        i = rfind(relativeVersionInformationPath, scriptGlobals.osDirSeparator)
        if i > -1: 
            manifest = relativeVersionInformationPath[i+1:]
        else:
            manifest = relativeVersionInformationPath
        extractFileFromZipToDir(warPath, relativeVersionInformationPath, tmpPath)
        version = grepFile(versionInformationRegex, tmpPath + scriptGlobals.osDirSeparator + manifest)
        revision = grepFile(revisionInformationRegex, tmpPath + scriptGlobals.osDirSeparator + manifest)
    elif os.path.isdir(warPath):
        #This is a exploded war directory
        version = grepFile(versionInformationRegex, warPath + scriptGlobals.osDirSeparator + relativeVersionInformationPath)
        revision = grepFile(revisionInformationRegex, warPath + scriptGlobals.osDirSeparator + relativeVersionInformationPath)
    else:
        return "UNKNOWN", "UNKNOWN"
    version = (re.sub(versionInformationRegex,"",version)).strip() #(version.replace(versionInformationRegex, "")).strip()
    revision = (re.sub(revisionInformationRegex,"",revision)).strip() #(revision.replace(revisionInformationRegex, "")).strip()
    return version, revision    


def getDbUpdateScriptsToRun(version, dbUpdateConfigParser):
    version = getCleanVersionNumber(version)
    log.debug("Retrieving scripts for version " + version)
    scripts = []
    brachesDefault = []
    branches = dbUpdateConfigParser.sections()
    for branch in branches:
        log.debug(" Checking branch section " + branch)
        if isVersionInBranch(version, branch):
            log.debug("  Matches branch section " + branch)
            versionPatterns = dbUpdateConfigParser.options(branch)
            filesStr = None
            defaultFilesStr = None
            for vpat in versionPatterns:
                log.debug("   Checking version pattern " + vpat)
                if vpat.strip().lower() == 'default':
                    defaultFilesStr = dbUpdateConfigParser.get(branch, vpat)
                elif re.match(vpat, version):
                    log.debug("    Matches version pattern " + vpat)
                    filesStr = dbUpdateConfigParser.get(branch, vpat)
                    if filesStr.strip().lower() == 'unsupported' :
                        log.debug("     Version not supported")
                        return False, scripts, brachesDefault
                break
            if filesStr is not None:
                files = filesStr.split(':')
            elif defaultFilesStr is not None:
                log.debug("    Matches default version")
                if defaultFilesStr.strip().lower() == 'unsupported' :
                    log.debug("     Version not supported")
                    return False, scripts, brachesDefault
                log.info("WARNING: Default migration scripts for branch "+branch+" have been added for execution")
                brachesDefault.append(branch)
                files = defaultFilesStr.split(':')
            else:
                return False, scripts, brachesDefault
            for f in files:
                if f[0] == '@':
                    log.debug("     Found reference to version " + f)
                    found, moreScripts, moreDefault = getDbUpdateScriptsToRun(f[1:], dbUpdateConfigParser)
                    if found:
                        scripts.extend(moreScripts)
                        brachesDefault.extend(moreDefault)
                    else:
                        return False, scripts, brachesDefault
                else:
                    log.debug("     Found script " + f)
                    scripts.append(f)
            return True, scripts, brachesDefault
    return False, scripts, brachesDefault

def getCleanVersionNumber(version):
    m = re.match('(\d+\.)+\d+', version)
    if(m): 
        log.debug('getCleanVersionNumber for "'+version+'" results to "'+m.group(0)+'"')
        return m.group(0)
    else: 
        log.debug('getCleanVersionNumber unable to detect version for "'+version+'"')
        return "0"

def isVersionInBranch(version, branch):
    ver = getCleanVersionNumber(version)
    branchPattern = string.replace(branch, '.', '\.')
    branchPattern = string.replace(branchPattern, 'x', '(\d+)')
    if re.match(branchPattern, ver):
        return True
    else:
        return False

def compareVersions(version1, version2):
    ver1 = getCleanVersionNumber(version1)
    ver2 = getCleanVersionNumber(version2)
    #print "Compare "+ver1+" to "+ver2
    if ver1 == ver2:
        return 0
    v1 = map(int, ver1.split("."))
    v2 = map(int, ver2.split("."))
    for i in range(0, min(len(v1), len(v2))):
        #print "  Compare #"+str(i)+": "+str(v1[i])+" , "+str(v2[i])
        if v1[i] > v2[i]:
            return 1
        elif v1[i] < v2[i]:
            return -1
    if len(v1) > len(v2):
        return 1
    elif len(v1) < len(v2):
        return -1
    else:
        return 0

def continueOrCancel(message):
    message = message + "\n\nSelect your action:\n\n(I) Continue execution \n(<any other key>) Raise error and get the option to rollback (NOTE: Some actions cannot be rolled back) "
    answer = getAnswerFromUser(message)
    if (re.compile('^i$', re.I)).match(answer):
        pass
    else:
        raise Exception

def confirmYesOrNo(message):
    message = message + "\n\nYour answer:\n\n(Y) Yes \n(<any other key>) No "
    answer = getAnswerFromUser(message)
    if (re.compile('^y$', re.I)).match(answer):
        return True
    else:
        return False

#class MergeSectionlessConfigFiles(Action):
#    '''
#    DO: Merge properties of primary and secondary property file to a new one (maintain props from primary file)
#    UNDO: Remove merged file (don't use primary or secondary file as the resulting merged) 
#    '''
#    def __init__(self, primaryFile, secondaryFile, mergedFile): 
#        log.debug(self.__class__.__name__ + " initialized")
#        self.primaryFile = primaryFile
#        self.secondaryFile = secondaryFile
#        self.mergedFile = mergedFile
#        Action.__init__(self)
#        
#    def __call__(self):
#        self.mergeSectionlessConfigFiles(self.primaryFile, self.secondaryFile, self.mergedFile)
#        
#    def undo(self):
#        deleteDirOrFile(self.mergedFile)
#        
#    def cleanup(self):
#        raise NotImplemented
#    
#    def report(self):
#        log.info("Merge properties from " + self.primaryFile + " and " + self.secondaryFile + " to " + self.mergedFile)
#
#    def mergeSectionlessConfigFiles(self,primaryFileName, secondaryFileName, mergedFileName):
#        primaryFP = open(primaryFileName, 'r')
#        secondaryFP = open(secondaryFileName, 'r')
#        mergedFP = open(mergedFileName, 'w+')
#        primaryCfg = ConfigParser()
#        primaryCfg.readfp(DummySectionPropertyFileWrapper(primaryFP))
#        
#        secondaryCfg = ConfigParser()
#        secondaryCfg.readfp(DummySectionPropertyFileWrapper(secondaryFP))
#        
#        for propName in secondaryCfg.options('DUMMY_SECTION'):
#            if primaryCfg.has_option('DUMMY_SECTION', propName):
#                continue
#            val = secondaryCfg.get('DUMMY_SECTION', propName)
#            mergedFP.write(propName + '=' + val)
#            #primaryCfg.set('DUMMY_SECTION', propName, val)
#        close(primaryFP)
#        close(secondaryFP)
#        close(mergedFP)
#
#class DummySectionPropertyFileWrapper(object):
#    def __init__(self, fp):
#        self.fp = fp
#        self.sechead = '[DUMMY_SECTION]\n'
#    def readline(self):
#        if self.sechead:
#            try: return self.sechead
#            finally: self.sechead = None
#        else: return self.fp.readline()
