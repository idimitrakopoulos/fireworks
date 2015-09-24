from lib.Toolkit import log, readPropertyFromPropertiesFile, scriptGlobals, initModuleClassFromString, readPropertyFromPropertiesFileWithFallback


class Module(object):

    '''
    classdocs
    '''

    def __init__(self, moduleFilename, modulePropertiesFilename, environmentPropertiesFilename):
        '''
        Constructor
        '''
        self.moduleFilename = moduleFilename
        self.name = readPropertyFromPropertiesFile("name", scriptGlobals.moduleSectionName, modulePropertiesFilename)        
        self.subModule = initModuleClassFromString(readPropertyFromPropertiesFile("moduleClass", scriptGlobals.moduleSectionName, modulePropertiesFilename), self.moduleFilename, modulePropertiesFilename, environmentPropertiesFilename)        
        self.launchType = readPropertyFromPropertiesFile("launchType", scriptGlobals.moduleSectionName, modulePropertiesFilename)

        self.preExecutionLogicClass = readPropertyFromPropertiesFileWithFallback("preExecutionLogicClass", scriptGlobals.moduleSectionName, modulePropertiesFilename, "preexeclogic.GenericPreExecLogic.GenericPreExecLogic")
        self.postExecutionLogicClass = readPropertyFromPropertiesFileWithFallback("postExecutionLogicClass", scriptGlobals.moduleSectionName, modulePropertiesFilename, "postexeclogic.GenericPostExecLogic.GenericPostExecLogic")

#        self.moduleCleanAB = readPropertyFromPropertiesFile("moduleCleanAB", scriptGlobals.moduleSectionName, modulePropertiesFilename)
#        self.moduleUpdateAB = readPropertyFromPropertiesFile("moduleUpdateAB", scriptGlobals.moduleSectionName, modulePropertiesFilename)
#        self.moduleStartAB = readPropertyFromPropertiesFile("moduleStartAB", scriptGlobals.moduleSectionName, modulePropertiesFilename)
#        self.moduleStopAB = readPropertyFromPropertiesFile("moduleStopAB", scriptGlobals.moduleSectionName, modulePropertiesFilename)
#        self.moduleRestartAB = readPropertyFromPropertiesFile("moduleRestartAB", scriptGlobals.moduleSectionName, modulePropertiesFilename)
#        self.moduleKillAB = readPropertyFromPropertiesFile("moduleKillAB", scriptGlobals.moduleSectionName, modulePropertiesFilename)
#        self.moduleStatusAB = readPropertyFromPropertiesFile("moduleStatusAB", scriptGlobals.moduleSectionName, modulePropertiesFilename)
#        self.moduleInfoAB = readPropertyFromPropertiesFile("moduleInfoAB", scriptGlobals.moduleSectionName, modulePropertiesFilename)
#        self.moduleLogAB = readPropertyFromPropertiesFile("moduleLogAB", scriptGlobals.moduleSectionName, modulePropertiesFilename)
#        self.moduleRollbackAB = readPropertyFromPropertiesFileWithFallback("moduleRollbackAB", scriptGlobals.moduleSectionName, modulePropertiesFilename, "actionbundles.GenericActionBundles.GenericRollbackAB")
#        self.moduleDebugAB = readPropertyFromPropertiesFile("moduleDebugAB", scriptGlobals.moduleSectionName, modulePropertiesFilename)

        self._actionBundleGroupWrappers = eval(readPropertyFromPropertiesFile("actionBundleGroupWrappers", scriptGlobals.moduleSectionName, modulePropertiesFilename))

        # Create internal actionbundle class structure
        self.actionBundleGroupClasses = {}

        # Using actionBundleGroupClasses create an internal dictionary with nested lists called actionBundleGroupClasses
        # For each action wrapper
        for k, v in self._actionBundleGroupWrappers.items():
            self.actionBundleGroupClasses[k] = []
            vs = v.split(",")
            for i in vs:
                # If value isnt empty then proceed
                if not i.strip() == '':
                    print "i is '" + i + "' "
                    # get python classnames that will be instantiated
                    className = readPropertyFromPropertiesFile(i.strip(), scriptGlobals.moduleSectionName, modulePropertiesFilename)
                    self.actionBundleGroupClasses[k].append(className)


        # File/Folder locations
        self._locations = eval(readPropertyFromPropertiesFile("locations", scriptGlobals.moduleSectionName, modulePropertiesFilename))

        self.relativeConfigurationFiles         = self._locations['relativeConfigurationFiles']
        self.relativeCopyableFilesOrFolders     = self._locations['relativeCopyableFilesOrFolders']
        self.relativeBackupOnlyFilesOrFolders   = self._locations['relativeBackupOnlyFilesOrFolders']
        self.relativeDatabaseInitFiles          = (self._locations['relativeDatabaseInitFiles']).split(',')
        self.relativeDatabaseUpgradeFilePath    = self._locations['relativeDatabaseUpgradeFilePath']
        self.relativeVersionInformationPath     = self._locations['relativeVersionInformationPath']
        self.relativeLogFilePath                = self._locations['relativeLogFilePath']
        self.relativeModulePropertiesPath       = self._locations['relativeModulePropertiesPath']

        self.versionInformationRegex = readPropertyFromPropertiesFile("versionInformationRegex", scriptGlobals.moduleSectionName, modulePropertiesFilename)
        self.revisionInformationRegex = readPropertyFromPropertiesFile("revisionInformationRegex", scriptGlobals.moduleSectionName, modulePropertiesFilename)        


        self.targetDeploymentPath = readPropertyFromPropertiesFile("TARGET_DEPLOYMENT_PATH", self.name, environmentPropertiesFilename)
        self.targetDeploymentProfile = readPropertyFromPropertiesFile("TARGET_DEPLOYMENT_PROFILE", self.name, environmentPropertiesFilename)        
        self.emailNotificationRecipientList = readPropertyFromPropertiesFileWithFallback("EMAIL_NOTIFICATION_RECIPIENT_LIST", self.name, environmentPropertiesFilename, "").split(",")
        self.friendlyServerName = readPropertyFromPropertiesFileWithFallback("FRIENDLY_SERVER_NAME", self.name, environmentPropertiesFilename, "n/a")
        
        self.executionContext = {}

        log.info(self.__class__.__name__ + " '" + self.name + "' initialized")