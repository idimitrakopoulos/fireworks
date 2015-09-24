from lib.Toolkit import log, scriptGlobals, createDirectoriesRecursively, sprintfOnDictionaryValues, readPropertyFromPropertiesFile, getProcessPIDByPath, die, grepFile, appendStringToEOF, generateGUID,\
    copyDirOrFile, getDirectoryRecursiveSize, getProcessPIDByPathAndIdentifier,\
    findNthSubstring, getAnswerFromUser,\
    readPropertyFromPropertiesFileWithFallback, getCurrentHostname, appendRequiredStringsToOracleSQLFile
import os, re, socket, platform, getpass
from actionbundles.ActionBundle import ActionBundle
from actions.FileSystemActions import CopyDirOrFile, ExtractZipToDir, CopyDirOrFile3, ExecuteOSCommand,\
    ExecuteOSCommandAndCaptureOutput, MoveDirOrFile
from actions.ConfigurationActions import ConfigureTemplateFile, CheckFileConfigurationIsComplete,\
    FinalReportingAction
from actions.DatabaseActions import RunOracleScriptFromFile, runOracleScript, RunOracleScript
from lib.ApplicationServer import ApplicationServer
from lib.FunStuff import informationAsciiHeader
import lib.OptParser
from lib.TabularResultOutput import indent
from notifications.CRMNotificationTemplates import detailedInstallationReportTemplate
from actions.NetworkActions import SendEmail


def getApplicationServerPID(module):
    # Initialize application server object
    appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

    # Check if JBOSS is running
    return getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier)


def populateApplicationConfigurationFiles(moduleName, configurationFileDictionary, unzippedPackagePath):
    for k, v in configurationFileDictionary.items():
        exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
        ConfigureTemplateFile(moduleName, lib.OptParser.options.envprops, exactExtractedLocation)
        CheckFileConfigurationIsComplete(exactExtractedLocation)


def copyApplicationFilesToTargetLocation(unzippedPackagePath, copyableFilesDictionary, targetDeploymentPath):
    for k, v in copyableFilesDictionary.items():
        exactSourceLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
        exactTargetLocation = targetDeploymentPath + scriptGlobals.osDirSeparator + v
        CopyDirOrFile(exactSourceLocation, exactTargetLocation)

def copyApplicationFilesFromTargetLocation(unzippedPackagePath, copyableFilesDictionary, targetDeploymentPath):
    for k, v in copyableFilesDictionary.items():
        exactSourceLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + v
        exactTargetLocation = targetDeploymentPath + scriptGlobals.osDirSeparator + k
        CopyDirOrFile3(exactSourceLocation, exactTargetLocation)

def extractOracleDatabaseCredentials(moduleName, envprops, usernameFieldName, passwordFieldName, connectionStringFieldName):
    # Import Clean DB script to Oracle DB
    dbUsername = readPropertyFromPropertiesFile(usernameFieldName, moduleName, envprops)
    dbPassword = readPropertyFromPropertiesFile(passwordFieldName, moduleName, envprops)

    tmpC = readPropertyFromPropertiesFile(connectionStringFieldName, moduleName, envprops)

    # If string is Clustered string
    if tmpC.lower().find("description") > 0:
        dbConnectionString = tmpC
    else:
        dbHost = tmpC[0:tmpC.find(":")]
        dbPort = tmpC[tmpC.find(":") + 1:tmpC.rfind(":")]
        dbSID = tmpC[tmpC.rfind(":") + 1:len(tmpC)]
        dbConnectionString = "(DESCRIPTION=(LOAD_BALANCE=yes)(ADDRESS=(PROTOCOL=TCP)(HOST=%s)(PORT=%s))(CONNECT_DATA=(SID=%s)))" % (
        dbHost, dbPort, dbSID)

    return (dbUsername, dbPassword, dbConnectionString)

def logOracleScriptInDBLog(scriptFilename, guid, action, moduleName, versionInfo, revisionInfo, oracleConnectionString):
    runOracleScript("INSERT INTO FIREWORKS_SCRIPT_LOG (INSTALLATION_ID, ACTION, MODULE_NAME, MODULE_VERSION, MODULE_REVISION, EXECUTED_SCRIPT, EXECUTED_ON) VALUES ('" + guid + "', '" + action + "', '" + moduleName + "', '" + versionInfo + "', '" + revisionInfo + "', '" + scriptFilename + "', CURRENT_TIMESTAMP);", oracleConnectionString, True, True)

def getLatestExecutedScript(versionInfo, majorVersionInfo, oracleConnectionString):
    return runOracleScript("SELECT EXECUTED_SCRIPT FROM FIREWORKS_SCRIPT_LOG WHERE EXECUTED_ON IN (SELECT MAX(EXECUTED_ON) FROM FIREWORKS_SCRIPT_LOG WHERE SUBSTR(MODULE_VERSION," + str(versionInfo.find("-") + 2) + "," + str(len(majorVersionInfo)) + ") = '" + majorVersionInfo + "');", oracleConnectionString, False, True)

def getVersionAndRevisionInfo(versionRegex, revisionRegex, rootPath, versionRelativeInformationPath):
    # Find version/revision info
    versionInfo = grepFile(versionRegex, rootPath + scriptGlobals.osDirSeparator + versionRelativeInformationPath)
    revisionInfo = grepFile(revisionRegex, rootPath + scriptGlobals.osDirSeparator + versionRelativeInformationPath)

    return (versionInfo.replace(versionRegex, "")).strip(), (revisionInfo.replace(revisionRegex, "")).strip()

def importCMSStructure(rootPath, cmsStructureImportToolLocation, host, port, username, cmsStructureFilename):
    cmsTool = rootPath + scriptGlobals.osDirSeparator + cmsStructureImportToolLocation
    ExecuteOSCommandAndCaptureOutput("java -jar " + cmsTool + " -host " + host + " -port " + port + " -user " + username + " -zipFile " + cmsStructureFilename, ["Exception", "faultCode"], None, None)

#class CRMCleanAB(ActionBundle):
#    '''
#    Perform a clean CRM installation
#    '''
#
#    def __init__(self, module):
#        '''
#        Constructor
#        '''
#        ActionBundle.__init__(self, module)
#
#        # Dont continue if application server is up
#        if getApplicationServerPID(module): die(
#            "The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")
#
#        # Generate a unique ActionBundle execution id
#        guid = generateGUID()
#        log.info("Unique ActionBundle execution ID generated: " + guid)
#
#        # Prepare directory to unpack package
#        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")
#
#        # CRM is a JBOSS webapp. Some paths have an %s to allow a configurable profile, so do a little sprintf to fix them
#        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
#        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)
#
#        # Extract CRM package into tmp dir
#        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)
#
#        # Get Version, Revision information
#        versionInfo, revisionInfo = getVersionAndRevisionInfo(module.versionInformationRegex, module.revisionInformationRegex, unzippedPackagePath, module.relativeVersionInformationPath)
#
#        # Populate Application Configuration files
#        populateApplicationConfigurationFiles(module.name, module.relativeConfigurationFiles, unzippedPackagePath)
#
#        # Copy Configuration Files to Target Location
#        copyApplicationFilesToTargetLocation(unzippedPackagePath, module.relativeConfigurationFiles, module.targetDeploymentPath)
#
#        # Copy Binary Files to Target Location
#        copyApplicationFilesToTargetLocation(unzippedPackagePath, module.relativeCopyableFilesOrFolders, module.targetDeploymentPath)
#
#        # Compose Oracle DB Connection String
#        oracleConnectionString = "%s/%s@%s" % (extractOracleDatabaseCredentials(module.name, lib.OptParser.options.envprops, "VNA_CRM_USERNAMEBASE", "VNA_CRM_PASSWORDBASE", "DBConnectionString"))
#
#        # Run DB init script(s)
#        for dbInitScript in module.relativeDatabaseInitFiles:
#            appendRequiredStringsToOracleSQLFile(unzippedPackagePath + scriptGlobals.osDirSeparator + dbInitScript)
#            RunOracleScriptFromFile(unzippedPackagePath + scriptGlobals.osDirSeparator + dbInitScript, oracleConnectionString)
#
#        # Add LOG table
#        RunOracleScriptFromFile(scriptGlobals.oracleLogTemplateFile, oracleConnectionString)
#
#        # Log DB init script(s)
#        for dbInitScript in module.relativeDatabaseInitFiles:
#            logOracleScriptInDBLog(dbInitScript, guid, lib.OptParser.options.action, module.name, versionInfo, revisionInfo, oracleConnectionString)
#
#        # Already existing upgrade scripts must be logged because in the upcoming upgrade we need to run from there on
#        log.info("Existing SQL patches will be logged in the log table so that the script will not run them again if you decise to update this version to latest")
#        ls = os.listdir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath)
#        ls.sort()
#        for patch in ls:
#            logOracleScriptInDBLog(patch, guid, lib.OptParser.options.action, module.name, versionInfo, revisionInfo, oracleConnectionString)
#
#        # Import CMS Structure
#        importCMSStructure(os.getcwd(), scriptGlobals.cmsStructureImportToolLocation, module.subModule.CMSHost, module.subModule.CMSPort, module.subModule.CMSUser, module.subModule.CMSStructureFilename)
#
#
#        # Construct the email notification
#        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress",
#                                                                 scriptGlobals.scriptVarSectionName,
#                                                                 lib.OptParser.options.envprops,
#                                                                 scriptGlobals.emailNotificationSenderAddress)
#        emailRecipients = scriptGlobals.globalNotificationEmailList
#        emailSubject = "CRM Clean Installation: " + module.name + "@" + getCurrentHostname() + " (" + module.friendlyServerName + ")"
#        emailText = detailedInstallationReportTemplate(module.name,
#                                                            lib.OptParser.options.action,
#                                                            getCurrentHostname(),
#                                                            os.getcwd(),
#                                                            guid,
#                                                            " ".join(platform.uname()),
#                                                            getpass.getuser(),
#                                                            versionInfo,
#                                                            revisionInfo,
#                                                            lib.OptParser.options.envprops)
#
#        # Email all required parties
#        SendEmail(emailSender,
#                  emailRecipients,
#                  emailSubject,
#                  emailText,
#                  scriptGlobals.smtpHost,
#                  scriptGlobals.smtpPort)
#
#        # end


#class CRMUpdateAB(ActionBundle):
#    '''
#    Perform an update of a CRM installation
#    '''
#
#    def __init__(self, module):
#        '''
#        Constructor
#        '''
#        ActionBundle.__init__(self, module)
#
#        # Dont continue if application server is up
#        if getApplicationServerPID(module): die(
#            "The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")
#
#        # Generate a unique ActionBundle execution id
#        guid = generateGUID()
#        log.info("Unique ActionBundle execution ID generated: " + guid)
#
#        # Since CRM is deployed on JBOSS some paths have an %s to allow a configurable
#        # profile, so do a little sprintf to fix them
#        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
#        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)
#
#
#        # Prepare directory to keep backups
#        previousVersionBackupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "previousVersionBackup")
#
#        # Backup Configuration Files to Target Location
#        copyApplicationFilesFromTargetLocation(module.targetDeploymentPath, module.relativeConfigurationFiles, previousVersionBackupPath)
#
#        # Backup Binary Files to Target Location
#        copyApplicationFilesFromTargetLocation(module.targetDeploymentPath, module.relativeCopyableFilesOrFolders, previousVersionBackupPath)
#
#        # Prepare directory to unpack package
#        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")
#
#        # Extract CRM package into tmp dir
#        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)
#
#        # Get Version, Revision information
#        versionInfo, revisionInfo = getVersionAndRevisionInfo(module.versionInformationRegex, module.revisionInformationRegex, unzippedPackagePath, module.relativeVersionInformationPath)
#        previousVersionInfo, previousRevisionInfo = getVersionAndRevisionInfo(module.versionInformationRegex, module.revisionInformationRegex, previousVersionBackupPath, module.relativeVersionInformationPath)
#        majorVersionInfo = versionInfo[versionInfo.find("-") + 1:findNthSubstring(versionInfo, ".", 2)]
#
#        # Compare current and new versions
#        log.info("Version currently installed    : " + previousVersionInfo)
#        log.info("Revision currently installed   : " + previousRevisionInfo)
#        log.info("Version to be installed        : " + versionInfo)
#        log.info("Revision to be installed       : " + revisionInfo)
#
#        # Populate Application Configuration files
#        populateApplicationConfigurationFiles(module.name, module.relativeConfigurationFiles, unzippedPackagePath)
#
#
#        # Copy Configuration Files to Target Location
#        copyApplicationFilesToTargetLocation(unzippedPackagePath, module.relativeConfigurationFiles, module.targetDeploymentPath)
#
#        # Copy Binary Files to Target Location
#        copyApplicationFilesToTargetLocation(unzippedPackagePath, module.relativeCopyableFilesOrFolders, module.targetDeploymentPath)
#
#        # Compose Oracle DB Connection String
#        oracleConnectionString = "%s/%s@%s" % (extractOracleDatabaseCredentials(module.name, lib.OptParser.options.envprops, "VNA_CRM_USERNAMEBASE", "VNA_CRM_PASSWORDBASE", "DBConnectionString"))
#
#        # Determine last executed script
#        result = getLatestExecutedScript(versionInfo, majorVersionInfo, oracleConnectionString)
#        lastExecutedPath, lastExecutedFilename = os.path.split(result.strip())
#
#        if ("no rows selected" in lastExecutedFilename):
#            answer = getAnswerFromUser("Unable to determine last executed script on '" + oracleConnectionString + "'. There is a possibility that the scripts in the log table are of an older major version than '" + majorVersionInfo + "'. (In this case you may want to run all the scripts in your upgrade folder '" + unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + "'). \n\nSelect your actions: \n(E) Execute all scripts in the upgrade folder in alphabetical order \n(<any other key>) Don't run any scripts and continue installation: ")
#            if (re.compile('^e$', re.I)).match(answer):
#                log.info("Running ALL scripts contained in '" + unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + "' in alphabetical order.")
#
#                # Run scripts on DB
#                ls = os.listdir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath)
#                ls.sort()
#                for patch in ls:
#                    appendRequiredStringsToOracleSQLFile(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + scriptGlobals.osDirSeparator + patch)
#                    RunOracleScriptFromFile(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + scriptGlobals.osDirSeparator + patch, oracleConnectionString)
#                    # Log executed scripts
#                    logOracleScriptInDBLog(patch, guid, lib.OptParser.options.action, module.name, versionInfo, revisionInfo, oracleConnectionString)
#
#        else:
#            log.info("According to log table, the last script executed on '" + oracleConnectionString + "' was '" + lastExecutedFilename + "'")
#
#            # Run scripts on DB
#            ls = os.listdir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath)
#            ls.sort()
#            found = False
#            for patch in ls:
#                if found:
#                    appendRequiredStringsToOracleSQLFile(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + scriptGlobals.osDirSeparator + patch)
#                    RunOracleScriptFromFile(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + scriptGlobals.osDirSeparator + patch, oracleConnectionString)
#                    # Log executed scripts
#                    logOracleScriptInDBLog(patch, guid, lib.OptParser.options.action, module.name, versionInfo, revisionInfo, oracleConnectionString)
#                if patch == lastExecutedFilename: found = True
#
#
#
#        # Construct the email notification
#        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress",
#                                                                 scriptGlobals.scriptVarSectionName,
#                                                                 lib.OptParser.options.envprops,
#                                                                 scriptGlobals.emailNotificationSenderAddress)
#        emailRecipients = scriptGlobals.globalNotificationEmailList
#        emailSubject = "CRM Update Installation: " + module.name + "@" + getCurrentHostname() + " (" + module.friendlyServerName + ")"
#        emailText = detailedInstallationReportTemplate(module.name,
#                                                             lib.OptParser.options.action,
#                                                             getCurrentHostname(),
#                                                             os.getcwd(),
#                                                             guid,
#                                                             " ".join(platform.uname()),
#                                                             getpass.getuser(),
#                                                             versionInfo,
#                                                             revisionInfo,
#                                                             lib.OptParser.options.envprops,
#                                                             previousVersionInfo,
#                                                             previousRevisionInfo)
#
#        # Email all required parties
#        SendEmail(emailSender,
#                  emailRecipients,
#                  emailSubject,
#                  emailText,
#                  scriptGlobals.smtpHost,
#                  scriptGlobals.smtpPort)
#
#
#        # end


class CRMInfoAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        # Initialize application server object
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Check if JBOSS is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier): die(
            "The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")

        # Since CRM is deployed on JBOSS some paths have an %s to allow a configurable 
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)

        # Prepare directory to keep backups
        previousVersionBackupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "previousVersionBackup")

        # Backup crm-deployment.properties from conf
        # Backup mgage.properties from conf
        # Backup jboss-log4j.xml from conf
        for k, v in module.relativeConfigurationFiles.items():
            exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            exactBackupLocation = previousVersionBackupPath + scriptGlobals.osDirSeparator + k
            copyDirOrFile(exactLocation, exactBackupLocation) # we do not to have do/undo actions for such operation

        # Backup crm-dtds from docs/dtd
        # Backup crm.war from deploy
        # Backup esb.jar from deploy/
        # Backup ROOT.WAR/crossdmain.xml from deploy/ROOT.WAR
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            exactBackupLocation = previousVersionBackupPath + scriptGlobals.osDirSeparator + k
            copyDirOrFile(exactLocation, exactBackupLocation) # we do not to have do/undo actions for such operation

        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(
            scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")

        # Extract CRM package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)


        # Determine last executed script in DB
        dbUsername = readPropertyFromPropertiesFile("VNA_CRM_USERNAMEBASE", module.name, lib.OptParser.options.envprops)
        dbPassword = readPropertyFromPropertiesFile("VNA_CRM_PASSWORDBASE", module.name, lib.OptParser.options.envprops)

        tmpC = readPropertyFromPropertiesFile("DBConnectionString", module.name, lib.OptParser.options.envprops)

        # If string is Clustered string
        if tmpC.lower().find("description") > 0:
            dbConnectionString = tmpC
        else:
            dbHost = tmpC[0:tmpC.find(":")]
            dbPort = tmpC[tmpC.find(":") + 1:tmpC.rfind(":")]
            dbSID = tmpC[tmpC.rfind(":") + 1:len(tmpC)]
            dbConnectionString = "(DESCRIPTION=(LOAD_BALANCE=yes)(ADDRESS=(PROTOCOL=TCP)(HOST=%s)(PORT=%s))(CONNECT_DATA=(SID=%s)))" % (
            dbHost, dbPort, dbSID)

        finalConnectionString = "%s/%s@%s" % (dbUsername, dbPassword, dbConnectionString)

        result = runOracleScript(
            "SELECT EXECUTED_SCRIPT FROM FIREWORKS_SCRIPT_LOG WHERE EXECUTED_ON IN (SELECT MAX(EXECUTED_ON) FROM FIREWORKS_SCRIPT_LOG);"
            , finalConnectionString, False, True)
        lastExecutedPath, lastExecutedFilename = os.path.split(result.strip())

        currentVersion = grepFile(module.versionInformationRegex,
                                  previousVersionBackupPath + scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        newVersion = grepFile(module.versionInformationRegex,
                              unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        currentRevision = grepFile(module.revisionInformationRegex,
                                   previousVersionBackupPath + scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        newRevision = grepFile(module.revisionInformationRegex,
                               unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)

        currentVersion = (currentVersion.replace(module.versionInformationRegex, "")).strip()
        newVersion = (newVersion.replace(module.versionInformationRegex, "")).strip()
        currentRevision = (currentRevision.replace(module.revisionInformationRegex, "")).strip()
        newRevision = (newRevision.replace(module.revisionInformationRegex, "")).strip()
        currentDirSize = getDirectoryRecursiveSize(previousVersionBackupPath)
        newDirSize = getDirectoryRecursiveSize(unzippedPackagePath)

        # Information Header
        log.info(informationAsciiHeader())

        labels = ('', 'Currently Installed Module', 'Module To Be Installed')
        data =\
        '''Version, %s, %s
           Revision, %s, %s
           Dir Size, %s, %s           
        ''' % (currentVersion, newVersion,
               currentRevision, newRevision,
               currentDirSize, newDirSize)

        rows = [row.strip().split(',')  for row in data.splitlines()]
        log.info("\n\n" + indent([labels] + rows, hasHeader=True))
        log.info("Last script executed on '" + finalConnectionString + "' was '" + lastExecutedFilename + "'")





class preCheckAB(ActionBundle):
    '''
    Perform a check to see if the server is up
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Dont continue if application server is up
        if getApplicationServerPID(module): die("The JBOSS server at '" + module.targetDeploymentPath + "' is up. Action will not continue")


class extractPackageAB(ActionBundle):
    '''
    Extract the module package
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")

        # Extract CRM package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)

        # Get Version, Revision information
        versionInfo, revisionInfo = getVersionAndRevisionInfo(module.versionInformationRegex, module.revisionInformationRegex, unzippedPackagePath, module.relativeVersionInformationPath)

        module.executionContext['unzippedPackagePath'] = unzippedPackagePath
        module.executionContext['versionInfo'] = versionInfo
        module.executionContext['revisionInfo'] = revisionInfo
        module.executionContext['guid'] = guid


class prepareJBOSSProfileVariablesAB(ActionBundle):
    '''
    Prepare locations to compensate for customizable JBOSS profiles
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # CRM is a JBOSS webapp. Some paths have an %s to allow a configurable profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeBackupOnlyFilesOrFolders, module.targetDeploymentProfile)

class preBackupJobsAB(ActionBundle):
    '''
    Perform pre backup jobs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Prepare directory to keep backups
        previousVersionBackupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "previousVersionBackup")

        module.executionContext['previousVersionBackupPath'] = previousVersionBackupPath


class postBackupJobsAB(ActionBundle):
    '''
    Perform post backup jobs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        previousVersionBackupPath = module.executionContext['previousVersionBackupPath']
        versionInfo = module.executionContext['versionInfo']
        revisionInfo = module.executionContext['revisionInfo']        

        previousVersionInfo, previousRevisionInfo = getVersionAndRevisionInfo(module.versionInformationRegex, module.revisionInformationRegex, previousVersionBackupPath, module.relativeVersionInformationPath)
        majorVersionInfo = versionInfo[versionInfo.find("-") + 1:findNthSubstring(versionInfo, ".", 3)]

        # Compare current and new versions
        log.info("Version currently installed    : " + previousVersionInfo)
        log.info("Revision currently installed   : " + previousRevisionInfo)
        log.info("Version to be installed        : " + versionInfo)
        log.info("Revision to be installed       : " + revisionInfo)

        module.executionContext['majorVersionInfo'] = majorVersionInfo
        module.executionContext['previousVersionInfo'] = previousVersionInfo
        module.executionContext['previousRevisionInfo'] = previousRevisionInfo

class applicationBackupAB(ActionBundle):
    '''
    Backup the application
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        previousVersionBackupPath = module.executionContext['previousVersionBackupPath']

        # Backup old runtime data
        copyApplicationFilesFromTargetLocation(module.targetDeploymentPath,module.relativeBackupOnlyFilesOrFolders,previousVersionBackupPath)
        # Backup Binary Files to Target Location
        copyApplicationFilesFromTargetLocation(module.targetDeploymentPath,module.relativeCopyableFilesOrFolders, previousVersionBackupPath)



class applicationInstallAB(ActionBundle):
    '''
    Install the application
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        unzippedPackagePath = module.executionContext['unzippedPackagePath']
        # Copy Binary Files to Target Location
        copyApplicationFilesToTargetLocation(unzippedPackagePath, module.relativeCopyableFilesOrFolders,module.targetDeploymentPath )
        copyApplicationFilesToTargetLocation(unzippedPackagePath, module.relativeBackupOnlyFilesOrFolders,module.targetDeploymentPath )


class configurationBackupAB(ActionBundle):
    '''
    Backup the configuration files
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        previousVersionBackupPath = module.executionContext['previousVersionBackupPath']

        # Backup Configuration Files to Target Location
        copyApplicationFilesFromTargetLocation(module.targetDeploymentPath, module.relativeConfigurationFiles, previousVersionBackupPath)



class configurationInstallAB(ActionBundle):
    '''
    Install the configuration files
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        unzippedPackagePath = module.executionContext['unzippedPackagePath']

        # Populate Application Configuration files
        populateApplicationConfigurationFiles(module.name, module.relativeConfigurationFiles, unzippedPackagePath)

        # Copy Configuration Files to Target Location
        copyApplicationFilesToTargetLocation(unzippedPackagePath, module.relativeConfigurationFiles, module.targetDeploymentPath)


class databaseCleanAB(ActionBundle):
    '''
    Clean the database schema
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        unzippedPackagePath = module.executionContext['unzippedPackagePath']
        versionInfo = module.executionContext['versionInfo']
        revisionInfo = module.executionContext['revisionInfo']
        guid = module.executionContext['guid']

        # Compose Oracle DB Connection String
        oracleConnectionString = "%s/%s@%s" % (extractOracleDatabaseCredentials(module.name, lib.OptParser.options.envprops, "VNA_CRM_USERNAMEBASE", "VNA_CRM_PASSWORDBASE", "DBConnectionString"))

        # Run DB init script(s)
        for dbInitScript in module.relativeDatabaseInitFiles:
            appendRequiredStringsToOracleSQLFile(unzippedPackagePath + scriptGlobals.osDirSeparator + dbInitScript)
            RunOracleScriptFromFile(unzippedPackagePath + scriptGlobals.osDirSeparator + dbInitScript, oracleConnectionString)

        # Add LOG table
        RunOracleScriptFromFile(scriptGlobals.oracleLogTemplateFile, oracleConnectionString)

        # Log DB init script(s)
        for dbInitScript in module.relativeDatabaseInitFiles:
            logOracleScriptInDBLog(dbInitScript, guid, lib.OptParser.options.action, module.name, versionInfo, revisionInfo, oracleConnectionString)

        # Already existing upgrade scripts must be logged because in the upcoming upgrade we need to run from there on
        log.info("Existing SQL patches will be logged in the log table so that the script will not run them again if you decise to update this version to latest")
        ls = os.listdir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath)
        ls.sort()
        for patch in ls:
            logOracleScriptInDBLog(patch, guid, lib.OptParser.options.action, module.name, versionInfo, revisionInfo, oracleConnectionString)


class databaseUpdateAB(ActionBundle):
    '''
    Update the database schema
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        unzippedPackagePath = module.executionContext['unzippedPackagePath']
        versionInfo = module.executionContext['versionInfo']
        revisionInfo = module.executionContext['revisionInfo']
        majorVersionInfo = module.executionContext['majorVersionInfo']
        guid = module.executionContext['guid']

        # Compose Oracle DB Connection String
        oracleConnectionString = "%s/%s@%s" % (extractOracleDatabaseCredentials(module.name, lib.OptParser.options.envprops, "VNA_CRM_USERNAMEBASE", "VNA_CRM_PASSWORDBASE", "DBConnectionString"))

        # Determine last executed script
        result = getLatestExecutedScript(versionInfo, majorVersionInfo, oracleConnectionString)
        lastExecutedPath, lastExecutedFilename = os.path.split(result.strip())

        if ("no rows selected" in lastExecutedFilename):
            answer = getAnswerFromUser("Unable to determine last executed script on '" + oracleConnectionString + "'. There is a possibility that the scripts in the log table are of an older major version than '" + majorVersionInfo + "'. (In this case you may want to run all the scripts in your upgrade folder '" + unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + "'). \n\nSelect your actions: \n(E) Execute all scripts in the upgrade folder in alphabetical order \n(<any other key>) Don't run any scripts and continue installation: ")
            if (re.compile('^e$', re.I)).match(answer):
                log.info("Running ALL scripts contained in '" + unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + "' in alphabetical order.")

                # Run scripts on DB
                ls = os.listdir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath)
                ls.sort()
                for patch in ls:
                    appendRequiredStringsToOracleSQLFile(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + scriptGlobals.osDirSeparator + patch)
                    RunOracleScriptFromFile(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + scriptGlobals.osDirSeparator + patch, oracleConnectionString)
                    # Log executed scripts
                    logOracleScriptInDBLog(patch, guid, lib.OptParser.options.action, module.name, versionInfo, revisionInfo, oracleConnectionString)

        else:
            log.info("According to log table, the last script executed on '" + oracleConnectionString + "' was '" + lastExecutedFilename + "'")

            # Run scripts on DB
            ls = os.listdir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath)
            ls.sort()
            found = False
            for patch in ls:
                if found:
                    appendRequiredStringsToOracleSQLFile(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + scriptGlobals.osDirSeparator + patch)
                    RunOracleScriptFromFile(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + scriptGlobals.osDirSeparator + patch, oracleConnectionString)
                    # Log executed scripts
                    logOracleScriptInDBLog(patch, guid, lib.OptParser.options.action, module.name, versionInfo, revisionInfo, oracleConnectionString)
                if patch == lastExecutedFilename: found = True




class cmsImportAB(ActionBundle):
    '''
    Import the CMS/CRM structure
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Import CMS Structure
        importCMSStructure(os.getcwd(), scriptGlobals.cmsStructureImportToolLocation, module.subModule.CMSHost, module.subModule.CMSPort, module.subModule.CMSUser, module.subModule.CMSStructureFilename)


class sendInstallationNotificationAB(ActionBundle):
    '''
    Send a notification for the installation
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        versionInfo = module.executionContext['versionInfo']
        revisionInfo = module.executionContext['revisionInfo']
#        previousVersionInfo = module.executionContext['previousVersionInfo']
#        previousRevisionInfo = module.executionContext['previousRevisionInfo']
        guid = module.executionContext['guid']

        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress",
                                                                 scriptGlobals.scriptVarSectionName,
                                                                 lib.OptParser.options.envprops,
                                                                 scriptGlobals.emailNotificationSenderAddress)

        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "CRM Installation: " + module.name + "@" + getCurrentHostname() + " (" + module.friendlyServerName + ")"
        emailText = detailedInstallationReportTemplate(module.name,
                                                            lib.OptParser.options.action,
                                                            getCurrentHostname(),
                                                            os.getcwd(),
                                                            guid,
                                                            " ".join(platform.uname()),
                                                            getpass.getuser(),
                                                            versionInfo,
                                                            revisionInfo,
                                                            lib.OptParser.options.envprops)

        # Email all required parties
        SendEmail(emailSender,
                  emailRecipients,
                  emailSubject,
                  emailText,
                  scriptGlobals.smtpHost,
                  scriptGlobals.smtpPort)