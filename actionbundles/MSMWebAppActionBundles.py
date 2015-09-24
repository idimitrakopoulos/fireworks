from lib.Toolkit import log, scriptGlobals, createDirectoriesRecursively, sprintfOnDictionaryValues, readPropertyFromPropertiesFile, getProcessPIDByPath, die, grepFile, appendStringToEOF, generateGUID, \
    copyDirOrFile, getDirectoryRecursiveSize, getProcessPIDByPathAndIdentifier,\
    findNthSubstring, getAnswerFromUser,\
    readPropertyFromPropertiesFileWithFallback, getCurrentHostname
import os, re, socket, platform, getpass
from actionbundles.ActionBundle import ActionBundle
from actions.FileSystemActions import CopyDirOrFile, ExtractZipToDir, CopyDirOrFile3, ExecuteOSCommand, \
    ExecuteOSCommandAndCaptureOutput, ChangePathPermissions, CopyDirOrFile2, CreateDirectory, DeleteDirOrFile
from actions.ConfigurationActions import ConfigureTemplateFile, CheckFileConfigurationIsComplete,\
    FinalReportingAction
from actions.DatabaseActions import RunOracleScriptFromFile, runOracleScript, RunOracleScript
from lib.ApplicationServer import ApplicationServer
from lib.FunStuff import informationAsciiHeader
import lib.OptParser
from lib.TabularResultOutput import indent
from notifications.MSMNotificationTemplates import detailedCleanInstallationReportTemplate,\
    detailedUpdateInstallationReportTemplate
from actions.NetworkActions import SendEmail



class MSMCleanAB(ActionBundle):
    '''
    Perform a clean MSM installation
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)
        
        # Initialize application server object
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)
        
        # Check if Tomcat is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier): die("\n\nThe Jboss server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")

        # Since MSM is deployed on JBOSS some paths have an %s to allow a configurable
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)

        #For JbosswebappPath = "/server/" + module.targetDeploymentProfile + "/deploy/" + module.subModule.name + ".war"
        # for Tomcat webappPath =  "/webapps/" + module.subModule.name
        webappPath =  "/webapps/" + module.subModule.name
        # Check if module exists.
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            if  exactTargetLocation.find(webappPath) != -1 :
                if os.path.isdir(exactTargetLocation):
                    log.info("\n##############################################################\n" + module.subModule.name
                             + " is already installed under:" + module.targetDeploymentPath
                             + ". Please manually backup and remove to run a clean installation (unless you want to update)\n##############################################################")
                    die()


        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")

        # Extract MSM package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)
        CreateDirectory(unzippedPackagePath + "/bin/" + module.subModule.name)
        ExtractZipToDir(unzippedPackagePath + "/bin/" + module.subModule.name + ".war", unzippedPackagePath + "/bin/" + module.subModule.name)

        # Configure xxx.properties in tmp/../conf using envprops
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops,  exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)

        # Copy relativeCopyableFilesOrFolders to specified locations on Server (values)
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)

        # Copy tmp/../conf/xxx.properties to to specified locations on Server (values)
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)

        # Find version/revision info
        revisionInfo = grepFile(module.revisionInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        revisionInfo = (revisionInfo.replace(module.revisionInformationRegex, "")).strip()
        versionInfo = grepFile(module.versionInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        versionInfo = (versionInfo.replace(module.versionInformationRegex, "")).strip()
        buildInfo = grepFile(module.buildInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        if buildInfo != None:
            buildInfo = (buildInfo.replace(module.buildInformationRegex, "")).strip()

        # Run CREATE/UPDATE/UPGRADE script
        if module.subModule.installUpdateScript != "":
            path1 = module.targetDeploymentPath + webappPath + "/" +  module.subModule.installUpdateScript
            ChangePathPermissions(path1, 0744)
            path1=path1 + " CREATE YES "
            ExecuteOSCommand(path1, None)

        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)        
        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "MSM Installation: " + module.subModule.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
        emailText = detailedCleanInstallationReportTemplate(module.subModule.name,
                                                    versionInfo,
                                                    lib.OptParser.options.action, 
                                                    getCurrentHostname(), 
                                                    os.getcwd(), 
                                                    guid,
                                                    " ".join(platform.uname()),
                                                    getpass.getuser(),
                                                    buildInfo,
                                                    revisionInfo,                                                    
                                                    lib.OptParser.options.envprops,
                                                    scriptGlobals.workingDir)
          
        # Email all required parties
        SendEmail(emailSender, 
                  emailRecipients,
                  emailSubject, 
                  emailText,
                  scriptGlobals.smtpHost, 
                  scriptGlobals.smtpPort)        
        
        # end

class MSMUpdateAB(ActionBundle):
    '''
    Perform an update of module
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Initialize application server object
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if Tomcat is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier): die("\n\nThe Jboss server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")

        # Since MSM is deployed on JBOSS some paths have an %s to allow a configurable
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)

        #For JbosswebappPath = "/server/" + module.targetDeploymentProfile + "/deploy/" + module.subModule.name + ".war"
        # for Tomcat webappPath =  "/webapps/" + module.subModule.name
        webappPath =  "/webapps/" + module.subModule.name
        exists="true"
        # Check if module exists.
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            if  exactTargetLocation.find(webappPath) != -1 :
                if not os.path.isdir(exactTargetLocation):
                    exists = "false"


        previousVersionInfo=""
        previousBuildInfo=""
        previousRevisionInfo=""
        if (exists == "true"):
        # Get Previous Hudson data
            previousManifilePath = module.targetDeploymentPath  + webappPath + "/META-INF/MANIFEST.MF"
            previousVersionInfo = grepFile(module.versionInformationRegex, previousManifilePath)
            previousBuildInfo = grepFile(module.buildInformationRegex, previousManifilePath)
            previousRevisionInfo = grepFile(module.revisionInformationRegex, previousManifilePath)
            previousVersionInfo = (previousVersionInfo.replace(module.versionInformationRegex, "")).strip()
            previousRevisionInfo = (previousRevisionInfo.replace(module.revisionInformationRegex, "")).strip()
            if previousBuildInfo != None:
                previousBuildInfo = (previousBuildInfo.replace(module.buildInformationRegex, "")).strip()

        # Prepare directory to keep backups
        previousVersionBackupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "previousVersionBackup")

        # Backup webapps
        if (lib.OptParser.action !="install-nodb-nobackup") and (exists == "true"):
            for k, v in module.relativeCopyableFilesOrFolders.items():
                exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
                exactBackupLocation = previousVersionBackupPath + scriptGlobals.osDirSeparator + k
                CopyDirOrFile3(exactLocation, exactBackupLocation)
                if  exactLocation.find(webappPath) != -1 :
                    DeleteDirOrFile(exactLocation)

        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")

        # Extract MSM package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)
        CreateDirectory(unzippedPackagePath + "/bin/" + module.subModule.name)
        ExtractZipToDir(unzippedPackagePath + "/bin/" + module.subModule.name + ".war", unzippedPackagePath + "/bin/" + module.subModule.name)

        # Configure xxx.properties in tmp/../conf using envprops
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops,  exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)

        # Copy relativeCopyableFilesOrFolders to specified locations on Server (values)
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)

        # Copy tmp/../conf/xxx.properties to to specified locations on Server (values)
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)

        # Find version/revision info
        revisionInfo = grepFile(module.revisionInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        revisionInfo = (revisionInfo.replace(module.revisionInformationRegex, "")).strip()
        versionInfo = grepFile(module.versionInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        versionInfo = (versionInfo.replace(module.versionInformationRegex, "")).strip()
        buildInfo = grepFile(module.buildInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        if buildInfo != None:
            buildInfo = (buildInfo.replace(module.buildInformationRegex, "")).strip()

        # CREATE/UPDATE/UPGRADE script
        if (lib.OptParser.action == "install-update" or lib.OptParser.action == "_customUpgrade" ) :
            if module.subModule.installUpdateScript != "":
                path2 = module.targetDeploymentPath  + webappPath + "/" +  module.subModule.installUpdateScript
                ChangePathPermissions(path2, 0744)
                if (lib.OptParser.action == "_customUpgrade"):
                    path2=path2 + " UPGRADE YES "
                else:
                    path2=path2 + " UPDATE YES "
                ExecuteOSCommand(path2, None)

        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "MSM Installation: " + module.subModule.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
        emailText = detailedUpdateInstallationReportTemplate(module.subModule.name,
                                                    versionInfo,
                                                    lib.OptParser.options.action,
                                                    getCurrentHostname(),
                                                    os.getcwd(),
                                                    guid,
                                                    " ".join(platform.uname()),
                                                    getpass.getuser(),
                                                    buildInfo,
                                                    revisionInfo,
                                                    lib.OptParser.options.envprops,
                                                    previousVersionInfo,
                                                    previousBuildInfo,
                                                    previousRevisionInfo,
                                                    scriptGlobals.workingDir)

        # Email all required parties
        SendEmail(emailSender,
                  emailRecipients,
                  emailSubject,
                  emailText,
                  scriptGlobals.smtpHost,
                  scriptGlobals.smtpPort)

        # end

class MSMConfigureAB(ActionBundle):
    '''
    Perform an update of module
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Initialize application server object
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if Tomcat is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier): die("\n\nThe Jboss server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")

        # Since MSM is deployed on JBOSS some paths have an %s to allow a configurable
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)

        #For JbosswebappPath = "/server/" + module.targetDeploymentProfile + "/deploy/" + module.subModule.name + ".war"
        # for Tomcat webappPath =  "/webapps/" + module.subModule.name
        webappPath =  "/webapps/" + module.subModule.name

        # Check if module exists.
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            if  exactTargetLocation.find(webappPath) != -1 :
                if not os.path.isdir(exactTargetLocation):
                    die("\n\n" + module.subModule.name + " is not installed under:" + module.targetDeploymentPath + ". Please first run a clean installation")

        # Get Previous Hudson data
        previousManifilePath = module.targetDeploymentPath + webappPath + "/META-INF/MANIFEST.MF"
        previousVersionInfo = grepFile(module.versionInformationRegex, previousManifilePath)
        previousBuildInfo = grepFile(module.buildInformationRegex, previousManifilePath)
        previousRevisionInfo = grepFile(module.revisionInformationRegex, previousManifilePath)
        previousVersionInfo = (previousVersionInfo.replace(module.versionInformationRegex, "")).strip()
        if previousBuildInfo != None:
            previousBuildInfo = (previousBuildInfo.replace(module.buildInformationRegex, "")).strip()

        previousRevisionInfo = (previousRevisionInfo.replace(module.revisionInformationRegex, "")).strip()

        # Prepare directory to keep backups
        previousVersionBackupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "previousVersionBackup")

        # Backup webapps
        if lib.OptParser.action !="install-nodb-nobackup":
            for k, v in module.relativeCopyableFilesOrFolders.items():
                exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
                exactBackupLocation = previousVersionBackupPath + scriptGlobals.osDirSeparator + k
                CopyDirOrFile3(exactLocation, exactBackupLocation)

        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")

        # Extract MSM package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)
        CreateDirectory(unzippedPackagePath + "/bin/" + module.subModule.name)
        ExtractZipToDir(unzippedPackagePath + "/bin/" + module.subModule.name + ".war", unzippedPackagePath + "/bin/" + module.subModule.name)

        # Configure xxx.properties in tmp/../conf using envprops
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops,  exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)

        # Copy tmp/../conf/xxx.properties to to specified locations on Server (values)
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)

        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "MSM Installation: " + module.subModule.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
        emailText = detailedUpdateInstallationReportTemplate(module.subModule.name,
                                                    previousVersionInfo,
                                                    lib.OptParser.options.action,
                                                    getCurrentHostname(),
                                                    os.getcwd(),
                                                    guid,
                                                    " ".join(platform.uname()),
                                                    getpass.getuser(),
                                                    previousBuildInfo,
                                                    previousRevisionInfo,
                                                    lib.OptParser.options.envprops,
                                                    previousVersionInfo,
                                                    previousBuildInfo,
                                                    previousRevisionInfo,
                                                    scriptGlobals.workingDir)

        # Email all required parties
        SendEmail(emailSender,
                  emailRecipients,
                  emailSubject,
                  emailText,
                  scriptGlobals.smtpHost,
                  scriptGlobals.smtpPort)

        # end

class MSMBackupAB(ActionBundle):
    '''
    Perform an update of module
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Initialize application server object
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if Tomcat is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier): die("The Jboss server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")

        # Since MSM is deployed on JBOSS some paths have an %s to allow a configurable
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)

        #For JbosswebappPath = "/server/" + module.targetDeploymentProfile + "/deploy/" + module.subModule.name + ".war"
        # for Tomcat webappPath =  "/webapps/" + module.subModule.name
        webappPath = "/webapps/" + module.subModule.name
		
        # Check if module exists.
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            if  exactTargetLocation.find(webappPath) != -1 :
                if not os.path.isdir(exactTargetLocation):
                    die("\n\n" + module.subModule.name + " is not installed under:" + module.targetDeploymentPath + ". Please first run a clean installation")

        # Get Previous Hudson data
        previousManifilePath =  module.targetDeploymentPath + webappPath +  "/META-INF/MANIFEST.MF"
        previousVersionInfo = grepFile(module.versionInformationRegex, previousManifilePath)
        previousBuildInfo = grepFile(module.buildInformationRegex, previousManifilePath)
        previousRevisionInfo = grepFile(module.revisionInformationRegex, previousManifilePath)
        previousVersionInfo = (previousVersionInfo.replace(module.versionInformationRegex, "")).strip()
        if previousBuildInfo != None:
            previousBuildInfo = (previousBuildInfo.replace(module.buildInformationRegex, "")).strip()

        previousRevisionInfo = (previousRevisionInfo.replace(module.revisionInformationRegex, "")).strip()

        # Prepare directory to keep backups
        previousVersionBackupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "previousVersionBackup")

        # Backup webapps
        if lib.OptParser.action !="install-nodb-nobackup":
            for k, v in module.relativeCopyableFilesOrFolders.items():
                exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
                exactBackupLocation = previousVersionBackupPath + scriptGlobals.osDirSeparator + k
                CopyDirOrFile3(exactLocation, exactBackupLocation)

        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "MSM Installation: " + module.subModule.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
        emailText = detailedUpdateInstallationReportTemplate(module.subModule.name,
                                                    previousVersionInfo,
                                                    lib.OptParser.options.action,
                                                    getCurrentHostname(),
                                                    os.getcwd(),
                                                    guid,
                                                    " ".join(platform.uname()),
                                                    getpass.getuser(),
                                                    previousBuildInfo,
                                                    previousRevisionInfo,
                                                    lib.OptParser.options.envprops,
                                                    previousVersionInfo,
                                                    previousBuildInfo,
                                                    previousRevisionInfo,
                                                    scriptGlobals.workingDir)

        # Email all required parties
        SendEmail(emailSender,
                  emailRecipients,
                  emailSubject,
                  emailText,
                  scriptGlobals.smtpHost,
                  scriptGlobals.smtpPort)

        # end

class MSMCustomSchemaUpdateAB(ActionBundle):
    '''
    Perform an CustomSchemaUpdate
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Initialize application server object
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if Tomcat is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier): die("\n\nThe Jboss server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")

        #For JbosswebappPath = "/server/" + module.targetDeploymentProfile + "/deploy/" + module.subModule.name + ".war"
        # for Tomcat webappPath =  "/webapps/" + module.subModule.name
        webappPath = "/webapps/" + module.subModule.name
		
        # Run script
        path2 = module.targetDeploymentPath + webappPath + "/" +  module.subModule.installUpdateScript
        ChangePathPermissions(path2, 0744)
        path2=path2 + " UPDATE YES "
        ExecuteOSCommand(path2, None)

        # Find version/revision info
        manifestFilePath=module.targetDeploymentPath + webappPath + "/META-INF/MANIFEST.MF"
        versionInfo = grepFile(module.versionInformationRegex, manifestFilePath)
        versionInfo = (versionInfo.replace(module.versionInformationRegex, "")).strip()
        revisionInfo = grepFile(module.revisionInformationRegex, manifestFilePath)
        revisionInfo = (revisionInfo.replace(module.revisionInformationRegex, "")).strip()
        buildInfo = grepFile(module.buildInformationRegex, manifestFilePath)
        if buildInfo != None:
            buildInfo = (buildInfo.replace(module.buildInformationRegex, "")).strip()

        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "MSM Installation: " + module.subModule.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
        emailText = detailedCleanInstallationReportTemplate(module.subModule.name,
                                                    versionInfo,
                                                    lib.OptParser.options.action,
                                                    getCurrentHostname(),
                                                    os.getcwd(),
                                                    guid,
                                                    " ".join(platform.uname()),
                                                    getpass.getuser(),
                                                    buildInfo,
                                                    revisionInfo,
                                                    lib.OptParser.options.envprops,
                                                    scriptGlobals.workingDir)

        # Email all required parties
        SendEmail(emailSender,
                  emailRecipients,
                  emailSubject,
                  emailText,
                  scriptGlobals.smtpHost,
                  scriptGlobals.smtpPort)

        # end

class MSMCustomSchemaCreateAB(ActionBundle):
    '''
    Perform an CustomSchemaCreate
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Initialize application server object
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if Jboss is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier): die("\n\nThe Jboss server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")

        #For JbosswebappPath = "/server/" + module.targetDeploymentProfile + "/deploy/" + module.subModule.name + ".war"
        # for Tomcat webappPath =  "/webapps/" + module.subModule.name
        webappPath = "/webapps/" + module.subModule.name
		
        # Run script
        path2 = module.targetDeploymentPath  + webappPath + "/" +  module.subModule.installUpdateScript
        ChangePathPermissions(path2, 0744)
        path2=path2 + " CREATE YES "
        ExecuteOSCommand(path2, None)

        # Find version/revision info
        manifestFilePath= module.targetDeploymentPath  + webappPath + "/META-INF/MANIFEST.MF"
        versionInfo = grepFile(module.versionInformationRegex, manifestFilePath)
        versionInfo = (versionInfo.replace(module.versionInformationRegex, "")).strip()
        revisionInfo = grepFile(module.revisionInformationRegex, manifestFilePath)
        revisionInfo = (revisionInfo.replace(module.revisionInformationRegex, "")).strip()
        buildInfo = grepFile(module.buildInformationRegex, manifestFilePath)
        if buildInfo != None:
            buildInfo = (buildInfo.replace(module.buildInformationRegex, "")).strip()

        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "MSM Installation: " + module.subModule.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
        emailText = detailedCleanInstallationReportTemplate(module.subModule.name,
                                                    versionInfo,
                                                    lib.OptParser.options.action,
                                                    getCurrentHostname(),
                                                    os.getcwd(),
                                                    guid,
                                                    " ".join(platform.uname()),
                                                    getpass.getuser(),
                                                    buildInfo,
                                                    revisionInfo,
                                                    lib.OptParser.options.envprops,
                                                    scriptGlobals.workingDir)                                                    

        # Email all required parties
        SendEmail(emailSender,
                  emailRecipients,
                  emailSubject,
                  emailText,
                  scriptGlobals.smtpHost,
                  scriptGlobals.smtpPort)

        # end

class MSMInfoAB(ActionBundle):
    '''
    Perform an update of module
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Initialize application server object
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Since MSM is deployed on JBOSS some paths have an %s to allow a configurable
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)        

        #For JbosswebappPath = "/server/" + module.targetDeploymentProfile + "/deploy/" + module.subModule.name + ".war"
        # for Tomcat webappPath =  "/webapps/" + module.subModule.name
        webappPath = "/webapps/" + module.subModule.name
		
        # Check if module exists.
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            if  exactTargetLocation.find(webappPath) != -1 :
                if not os.path.isdir(exactTargetLocation):
                    die("\n\n" + module.subModule.name + " is not installed under:" + module.targetDeploymentPath + ". Please first run a clean installation")

        # Get Previous Hudson data
        previousManifilePath = module.targetDeploymentPath + webappPath + "/META-INF/MANIFEST.MF"
        previousVersionInfo = grepFile(module.versionInformationRegex, previousManifilePath)
        previousBuildInfo = grepFile(module.buildInformationRegex, previousManifilePath)
        previousRevisionInfo = grepFile(module.revisionInformationRegex, previousManifilePath)
        previousRevisionInfo = (previousRevisionInfo.replace(module.revisionInformationRegex, "")).strip()
        previousVersionInfo = (previousVersionInfo.replace(module.versionInformationRegex, "")).strip()
        if previousBuildInfo != None:
            previousBuildInfo = (previousBuildInfo.replace(module.buildInformationRegex, "")).strip()

        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "MSM Installation: " + module.subModule.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
        emailText = detailedCleanInstallationReportTemplate(module.subModule.name,
                                                    previousVersionInfo,
                                                    lib.OptParser.options.action,
                                                    getCurrentHostname(),
                                                    os.getcwd(),
                                                    guid,
                                                    " ".join(platform.uname()),
                                                    getpass.getuser(),
                                                    previousBuildInfo,
                                                    previousRevisionInfo,
                                                    lib.OptParser.options.envprops,
                                                    scriptGlobals.workingDir)

        # Email all required parties
        SendEmail(emailSender,
                  emailRecipients,
                  emailSubject,
                  emailText,
                  scriptGlobals.smtpHost,
                  scriptGlobals.smtpPort)

        # end


