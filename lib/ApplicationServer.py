from lib.Toolkit import log, readPropertyFromPropertiesFile, scriptGlobals, sprintfOnListValues
import lib.OptParser

class ApplicationServer(object):
    '''
    classdocs
    '''
    appServerName = ""
    startCommand = ""
    shutdownCommand = ""
    binPath = ""
    deployLocation = ""
    configurationLocation = ""


    def __init__(self, module, applicationServerPropertiesFilename):
        '''
        Constructor
        '''

        if module.launchType != "standalone":
            self.appServerName = module.launchType
            self.startCommand = readPropertyFromPropertiesFile("startCommand", self.appServerName, applicationServerPropertiesFilename)
            self.shutdownCommand = readPropertyFromPropertiesFile("shutdownCommand", self.appServerName, applicationServerPropertiesFilename)
            self.binPath = readPropertyFromPropertiesFile("binPath", self.appServerName, applicationServerPropertiesFilename)
            self.configurationLocation = readPropertyFromPropertiesFile("configurationLocation", self.appServerName, applicationServerPropertiesFilename)
            self.deployLocation = readPropertyFromPropertiesFile("deployLocation", self.appServerName, applicationServerPropertiesFilename)
            self.relativeCacheFolders = readPropertyFromPropertiesFile("relativeCacheFolders", self.appServerName, applicationServerPropertiesFilename)
            self.processIdentifier = readPropertyFromPropertiesFile("processIdentifier", self.appServerName, applicationServerPropertiesFilename)
        else:
            self.processIdentifier = module.subModule.processIdentifier
            self.appServerName = module.subModule.name

        # Custom JBOSS profile requested by my friend Chris Skopelitis :-)
        if self.appServerName == "jboss": 
            profile = module.targetDeploymentProfile
            self.deployLocation = self.deployLocation % (profile)
            self.configurationLocation = self.configurationLocation % (profile)  
            self.relativeCacheFolders = sprintfOnListValues(self.relativeCacheFolders.split(","), profile)

        log.info("ApplicationServer '" + self.appServerName + "' class initialized using '" + applicationServerPropertiesFilename + "' conf file")