from lib.Toolkit import log, scriptGlobals, createDirectoriesRecursively, sprintfOnDictionaryValues, readPropertyFromPropertiesFile, getProcessPIDByPath, die, grepFile, appendStringToEOF, generateGUID, \
    copyDirOrFile, getDirectoryRecursiveSize, getProcessPIDByIdentifier, logExecute,getProcessPIDByPathAndIdentifier,\
    findNthSubstring, getAnswerFromUser, killProcess, runProcess,\
    readPropertyFromPropertiesFileWithFallback, getCurrentHostname
import os,platform, getpass
from actionbundles.ActionBundle import ActionBundle
from actions.FileSystemActions import CopyDirOrFile, ExtractZipToDir, CopyDirOrFile3, ExecuteOSCommand, deleteDirOrFile, \
    ExecuteOSCommandAndCaptureOutput, ChangePathPermissions, CopyDirOrFile2, CreateDirectory, DeleteDirOrFile, ExtractFileFromZipToDir
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
from notifications.GenericNotificationTemplates import killApplicationServerNotificationTemplate, startApplicationServerNotificationTemplate



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
       # appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if Server is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, module.subModule.processIdentifier): die("\n\nThe " + module.subModule.name + " server at '" + module.targetDeploymentPath + "' is up. Installation will not continue\n")

        # Check if module exists.
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            if os.path.isdir(exactTargetLocation):
                log.info("\n###############################################################################################\n" + module.subModule.name
                        + " is already installed under:" + module.targetDeploymentPath
                        + ". Please manually backup and remove to run a clean installation (unless you want to update)\n###############################################################################################")
                die()
					
        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")

        # Extract MSM package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)

        filenameToExtract = "META-INF/MANIFEST.MF"
        zipFilename = unzippedPackagePath +  "/bin/" + module.subModule.name + "/lib/" + module.subModule.name +".jar"
        location = unzippedPackagePath +  "/bin/" + module.subModule.name + "/META-INF"
        ExtractFileFromZipToDir(zipFilename, filenameToExtract, location)

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

        if (module.subModule.name == "mrouter"):
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + module._locations['relativeStartupScript']
            ChangePathPermissions(exactExtractedLocation, 0777)
            CopyDirOrFile2(exactExtractedLocation, module.targetDeploymentPath)

        # Find version/revision info
        versionInfo = grepFile(module.versionInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        versionInfo = (versionInfo.replace(module.versionInformationRegex, "")).strip()
        revisionInfo = grepFile(module.revisionInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        revisionInfo = (revisionInfo.replace(module.revisionInformationRegex, "")).strip()
        buildInfo = grepFile(module.buildInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        if buildInfo != None:
            buildInfo = (buildInfo.replace(module.buildInformationRegex, "")).strip()


        moduleDeployPath = module.targetDeploymentPath  + "/"  + module.subModule.name
        path1 = moduleDeployPath +  "/bin"
        ChangePathPermissions(path1, 0744)
        path2 = moduleDeployPath +  "/"  + module.subModule.installUpdateScript
        path2=path2 + " CREATE YES "
        ExecuteOSCommand(path2, None)
  ##ExecuteOSCommandAndCaptureOutput(path1,"ERROR", None, None)
  ##THIS    ExecuteOSCommand(path1, None)
  ##ExecuteOSCommandAndCaptureOutput("cd " + path1, None, None)

        
        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)        
        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "MSM Installation: " + module.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
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

class MSMConfigureAB(ActionBundle):
    '''
    Perform a configuration of MSM module
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if standalone is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, module.subModule.processIdentifier): die("\n\nThe " + module.subModule.name + " server at '" + module.targetDeploymentPath + "' is up. Configuration will not continue\n")

        # Check if module is already installed
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            if not os.path.isdir(exactLocation):
                die(module.subModule.name + " is Not already installed to:" + module.targetDeploymentPath + ". Maybe you want to make a clean Installation !!")

        # Get Previous Hudson data
        previousManifilePath = module.targetDeploymentPath + scriptGlobals.osDirSeparator + module.subModule.name + scriptGlobals.osDirSeparator + "META-INF" + scriptGlobals.osDirSeparator + "MANIFEST.MF"
        previousVersionInfo = grepFile(module.versionInformationRegex, previousManifilePath)
        previousBuildInfo = grepFile(module.buildInformationRegex, previousManifilePath)
        previousRevisionInfo = grepFile(module.revisionInformationRegex, previousManifilePath)
        previousVersionInfo = (previousVersionInfo.replace(module.versionInformationRegex, "")).strip()
        if previousBuildInfo != None:
            previousBuildInfo = (previousBuildInfo.replace(module.buildInformationRegex, "")).strip()

        previousRevisionInfo = (previousRevisionInfo.replace(module.revisionInformationRegex, "")).strip()

        # Prepare directory to keep backups
        previousVersionBackupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "previousVersionBackup")


        # Backup standalone
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            exactBackupLocation = previousVersionBackupPath + scriptGlobals.osDirSeparator + k
            CopyDirOrFile3(exactLocation, exactBackupLocation)
        #    if  exactLocation.find(module.subModule.name) != -1 :
        #        DeleteDirOrFile(exactLocation)

        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")

        # Extract MSM package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)

        filenameToExtract = "META-INF/MANIFEST.MF"
        zipFilename = unzippedPackagePath +  "/bin/" + module.subModule.name + "/lib/" + module.subModule.name +".jar"
        location = unzippedPackagePath +  "/bin/" + module.subModule.name + "/META-INF"
        ExtractFileFromZipToDir(zipFilename, filenameToExtract, location)


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
        emailSubject = "MSM Installation: " + module.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
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
#        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if standalone is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, module.subModule.processIdentifier): die("\n\nThe " + module.subModule.name + " server at '" + module.targetDeploymentPath + "' is up. Installation will not continue\n")

        exists="true"
        # Check if module is already installed
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            if not os.path.isdir(exactLocation):
                exists = "false"
                #die(module.subModule.name + " is Not already installed to:" + module.targetDeploymentPath + ". Maybe you want to make a clean Installation !!")

        previousVersionInfo=""
        previousBuildInfo=""
        previousRevisionInfo=""
        if (exists == "true"):
        # Get Previous Hudson data
            previousManifilePath = module.targetDeploymentPath + scriptGlobals.osDirSeparator + module.subModule.name + scriptGlobals.osDirSeparator + "META-INF" + scriptGlobals.osDirSeparator + "MANIFEST.MF"
            previousVersionInfo = grepFile(module.versionInformationRegex, previousManifilePath)
            previousBuildInfo = grepFile(module.buildInformationRegex, previousManifilePath)
            previousRevisionInfo = grepFile(module.revisionInformationRegex, previousManifilePath)
            previousVersionInfo = (previousVersionInfo.replace(module.versionInformationRegex, "")).strip()
            previousRevisionInfo = (previousRevisionInfo.replace(module.revisionInformationRegex, "")).strip()
            if previousBuildInfo != None:
                previousBuildInfo = (previousBuildInfo.replace(module.buildInformationRegex, "")).strip()

        # Prepare directory to keep backups
        previousVersionBackupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "previousVersionBackup")


        # Backup standalone
        if (lib.OptParser.action !="install-nodb-nobackup" and exists == "true"):
            for k, v in module.relativeCopyableFilesOrFolders.items():
                exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
                exactBackupLocation = previousVersionBackupPath + scriptGlobals.osDirSeparator + k
                CopyDirOrFile3(exactLocation, exactBackupLocation)
                if  exactLocation.find(module.subModule.name) != -1 :
                    DeleteDirOrFile(exactLocation)

        # Prepare directory to unpack package
        unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")

        # Extract MSM package into tmp dir
        ExtractZipToDir(module.moduleFilename, unzippedPackagePath)
 #       CreateDirectory(unzippedPackagePath + "/bin/" + module.subModule.name)
 #       ExtractZipToDir(unzippedPackagePath + "/bin/" + module.subModule.name + ".war", unzippedPackagePath + "/bin/" + module.subModule.name)


        filenameToExtract = "META-INF/MANIFEST.MF"
        zipFilename = unzippedPackagePath +  "/bin/" + module.subModule.name + "/lib/" + module.subModule.name +".jar"
        location = unzippedPackagePath +  "/bin/" + module.subModule.name + "/META-INF"
        ExtractFileFromZipToDir(zipFilename, filenameToExtract, location)


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

        if (module.subModule.name == "mrouter"):
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + module._locations['relativeStartupScript']
            ChangePathPermissions(exactExtractedLocation, 0777)
            CopyDirOrFile2(exactExtractedLocation, module.targetDeploymentPath)

        path1 = module.targetDeploymentPath  + "/"  + module.subModule.name +  "/bin"
        ChangePathPermissions(path1, 0744)

        # Find version/revision info
        versionInfo = grepFile(module.versionInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        versionInfo = (versionInfo.replace(module.versionInformationRegex, "")).strip()
        revisionInfo = grepFile(module.revisionInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        revisionInfo = (revisionInfo.replace(module.revisionInformationRegex, "")).strip()
        buildInfo = grepFile(module.buildInformationRegex, unzippedPackagePath +  scriptGlobals.osDirSeparator + module.relativeVersionInformationPath)
        if buildInfo != None:
            buildInfo = (buildInfo.replace(module.buildInformationRegex, "")).strip()

        if (lib.OptParser.action == "install-update" or lib.OptParser.action == "_customUpgrade"):
            moduleDeployPath = module.targetDeploymentPath  + "/"  + module.subModule.name
            path1 = moduleDeployPath +  "/bin"
            ChangePathPermissions(path1, 0744)
            path2 = moduleDeployPath +  "/"  + module.subModule.installUpdateScript
            if (lib.OptParser.action == "_customUpgrade"):
                path2=path2 + " UPGRADE YES "
            else:
                path2=path2 + " UPDATE YES "
            ExecuteOSCommand(path2, None)

        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "MSM Installation: " + module.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
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

class MSMBackupAB(ActionBundle):
    '''
    Perform an Backup of module
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Initialize application server object
#        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if standalone is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, module.subModule.processIdentifier): die("\n\nThe " + module.subModule.name + " server at '" + module.targetDeploymentPath + "' is up. Installation will not continue\n")

        # Check if module is already installed
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            if not os.path.isdir(exactLocation):
                die(module.subModule.name + " is Not already installed to:" + module.targetDeploymentPath + ". Maybe you want to make a clean Installation !!")

        # Get Previous Hudson data
        previousManifilePath = module.targetDeploymentPath + scriptGlobals.osDirSeparator + module.subModule.name + scriptGlobals.osDirSeparator + "META-INF" + scriptGlobals.osDirSeparator + "MANIFEST.MF"
        previousVersionInfo = grepFile(module.versionInformationRegex, previousManifilePath)
        previousBuildInfo = grepFile(module.buildInformationRegex, previousManifilePath)
        previousRevisionInfo = grepFile(module.revisionInformationRegex, previousManifilePath)
        previousVersionInfo = (previousVersionInfo.replace(module.versionInformationRegex, "")).strip()
        if previousBuildInfo != None:
            previousBuildInfo = (previousBuildInfo.replace(module.buildInformationRegex, "")).strip()

        previousRevisionInfo = (previousRevisionInfo.replace(module.revisionInformationRegex, "")).strip()

        # Prepare directory to keep backups
        previousVersionBackupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "previousVersionBackup")

        # Backup standalone
        if lib.OptParser.action !="install-nodb-nobackup":
            for k, v in module.relativeCopyableFilesOrFolders.items():
                exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
                exactBackupLocation = previousVersionBackupPath + scriptGlobals.osDirSeparator + k
                CopyDirOrFile3(exactLocation, exactBackupLocation)

       # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "MSM Installation: " + module.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
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
        # appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if Server is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, module.subModule.processIdentifier): die("\n\nThe " + module.subModule.name + " server at '" + module.targetDeploymentPath + "' is up. Installation will not continue\n")

        # Run script
        moduleDeployPath = module.targetDeploymentPath  + "/"  + module.subModule.name
        path2 = moduleDeployPath +  "/"  + module.subModule.installUpdateScript
        ChangePathPermissions(path2, 0744)
        path2=path2 + " UPDATE YES "
        ExecuteOSCommand(path2, None)

        # Find version/revision info
        manifestFilePath=moduleDeployPath + "/META-INF/MANIFEST.MF"
        versionInfo = grepFile(module.versionInformationRegex, manifestFilePath)
        buildInfo = grepFile(module.buildInformationRegex, manifestFilePath)
        revisionInfo = grepFile(module.revisionInformationRegex, manifestFilePath)

        versionInfo = (versionInfo.replace(module.versionInformationRegex, "")).strip()
        if buildInfo != None:
            buildInfo = (buildInfo.replace(module.buildInformationRegex, "")).strip()

        revisionInfo = (revisionInfo.replace(module.revisionInformationRegex, "")).strip()

        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "MSM Installation: " + module.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
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
        # appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if Server is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, module.subModule.processIdentifier): die("\n\nThe " + module.subModule.name + " server at '" + module.targetDeploymentPath + "' is up. Installation will not continue\n")

        # Run script
        moduleDeployPath = module.targetDeploymentPath  + "/"  + module.subModule.name
        path2 = moduleDeployPath +  "/"  + module.subModule.installUpdateScript
        ChangePathPermissions(path2, 0744)
        path2=path2 + " CREATE YES "
        ExecuteOSCommand(path2, None)

        # Find version/revision info
        manifestFilePath=moduleDeployPath + "/META-INF/MANIFEST.MF"
        versionInfo = grepFile(module.versionInformationRegex, manifestFilePath)
        buildInfo = grepFile(module.buildInformationRegex, manifestFilePath)
        revisionInfo = grepFile(module.revisionInformationRegex, manifestFilePath)

        versionInfo = (versionInfo.replace(module.versionInformationRegex, "")).strip()
        if buildInfo != None:
            buildInfo = (buildInfo.replace(module.buildInformationRegex, "")).strip()

        revisionInfo = (revisionInfo.replace(module.revisionInformationRegex, "")).strip()

        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
        emailRecipients = scriptGlobals.globalNotificationEmailList
        emailSubject = "MSM Installation: " + module.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
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

class MSMStandaloneServerKillAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        guid = generateGUID()


        log.info("Unique ActionBundle execution ID generated: " + guid)

        pid = getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, module.subModule.processIdentifier)

        # If process exists...
        if pid:

            # Kill process using pid
            killProcess(pid)

            # Construct the email notification
            emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
            emailRecipients = module.emailNotificationRecipientList
            emailSubject = "Server KILL: " + module.subModule.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
            emailText = killApplicationServerNotificationTemplate(module.name, getCurrentHostname(), guid)


            # Email all required parties
            SendEmail(emailSender,
                      emailRecipients,
                      emailSubject,
                      emailText,
                      scriptGlobals.smtpHost,
                      scriptGlobals.smtpPort)

class MSMStandaloneServerStartAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

      #  appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)
        pid = getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, module.subModule.processIdentifier)

        bin_path=module.targetDeploymentPath  + "/"  + module.subModule.name +  "/bin/"

        if pid:
            log.error("\n\nAlready existing process running from path '" + module.targetDeploymentPath + "' with pid '" + pid + "'.\n")
        else:
            # Delete all cached directories
            log.info("Proceeding to delete nohup file")
            try:
                    deleteDirOrFile(bin_path + "nohup.out")
            except OSError: # If directory doesn't exist ignore the raised error
                pass

            # Change directory to run the binary from inside the binpath
            pwd = os.getcwd()
            os.chdir(bin_path)
            ChangePathPermissions(bin_path + "start.sh", 0744)
            runProcess("nohup ./start.sh")
            os.chdir(pwd)

            # Construct the email notification
            emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
            emailRecipients = module.emailNotificationRecipientList
            emailSubject = "Server START: " + module.subModule.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
            emailText = startApplicationServerNotificationTemplate(module.name, getCurrentHostname(), guid)

            # Email all required parties
            SendEmail(emailSender,
                      emailRecipients,
                      emailSubject,
                      emailText,
                      scriptGlobals.smtpHost,
                      scriptGlobals.smtpPort)

class MSMStandaloneServerRestartAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

      #  appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)
        pid = getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, module.subModule.processIdentifier)

        bin_path=module.targetDeploymentPath  + "/"  + module.subModule.name +  "/bin/"

        if pid:
            log.info("\n\nAlready existing process running from path '" + module.targetDeploymentPath + "' with pid '" + pid + "'.\n")
            log.info("\n\Proceeding with Killing the Server")
            # Kill process using pid
            killProcess(pid)

        # Delete all cached directories
        log.info("Proceeding to delete nohup file")
        try:
            deleteDirOrFile(bin_path + "nohup.out")
        except OSError: # If directory doesn't exist ignore the raised error
                pass

        # Change directory to run the binary from inside the binpath
        pwd = os.getcwd()
        os.chdir(bin_path)
        ChangePathPermissions(bin_path + "start.sh", 0744)
        runProcess("nohup ./start.sh")
        os.chdir(pwd)

        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
        emailRecipients = module.emailNotificationRecipientList
        emailSubject = "Server START: " + module.subModule.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
        emailText = startApplicationServerNotificationTemplate(module.name, getCurrentHostname(), guid)

        # Email all required parties
        SendEmail(emailSender,
                      emailRecipients,
                      emailSubject,
                      emailText,
                      scriptGlobals.smtpHost,
                      scriptGlobals.smtpPort)


class MSMStandaloneServerStatusAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
   #     appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)
        pid = getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, module.subModule.processIdentifier)

        if pid:
            log.info("\n\n################################### " + module.subModule.name + " is Up with pid '" + pid + " ###################################\n")
        else:
            log.info("\n\n################################### " + module.subModule.name + " is Down ###################################\n")

class MSMStandaloneServerLogTailAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''

        for line in os.popen("echo $HOME"):
            fields = line.split()


        logpath = fields[0] + "/logs/" + module.relativeLogFilePath

        #logpath = module.relativeLogFilePath % (module.targetDeploymentProfile)
        logExecute("tail -f " + logpath)

class MSMInfoAB(ActionBundle):
    '''
    Perform a configuration of MSM module
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        ActionBundle.__init__(self, module)

        # Generate a unique ActionBundle execution id
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if standalone is running
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, module.subModule.processIdentifier): die("\n\nThe " + module.subModule.name + " server at '" + module.targetDeploymentPath + "' is up. Configuration will not continue\n")

        # Check if module is already installed
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v
            if not os.path.isdir(exactLocation):
                die(module.subModule.name + " is Not already installed to:" + module.targetDeploymentPath + ". Maybe you want to make a clean Installation !!")

        # Get Previous Hudson data
        previousManifilePath = module.targetDeploymentPath + scriptGlobals.osDirSeparator + module.subModule.name + scriptGlobals.osDirSeparator + "META-INF" + scriptGlobals.osDirSeparator + "MANIFEST.MF"
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
        emailSubject = "MSM Installation: " + module.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
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