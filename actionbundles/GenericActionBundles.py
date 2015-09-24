from actions.FileSystemActions import MoveDirOrFile, CreateDirectoriesRecursively, CreateDirectory, ChangePathPermissions
from lib.Toolkit import log, scriptGlobals, logExecute, grepFile,\
    deleteDirOrFile, launchHTTPServer, initClassFromStringWithModule,\
    generateGUID, readPropertyFromPropertiesFileWithFallback, getCurrentHostname, deserializeListFromFile, die, RollbackTriggerException, createDirectoriesRecursively, terminateProcess
from lib.Toolkit import killProcess, runProcess, getProcessPIDByPath, getProcessPIDByPathAndIdentifier
from actionbundles.ActionBundle import ActionBundle
from lib.ApplicationServer import ApplicationServer
import os, time, socket
from lib.Timer import Timer
import lib.OptParser
from lib.FireworksHTTPServer import FireworksHTTPRequestHandler
from actions.NetworkActions import SendEmail
from notifications.GenericNotificationTemplates import restartCancellationNotificationTemplate, restartPendingNotificationTemplate,\
    killApplicationServerNotificationTemplate,\
    stopApplicationServerNotificationTemplate,\
    startApplicationServerNotificationTemplate

class GenericApplicationServerStartAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)
                      
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)
        pid = getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier)
        
        if pid: 
            log.error("Already existing process running from path '" + module.targetDeploymentPath + "' with pid '" + pid + "'.")
        else:
            # Delete all cached directories
            log.info("Proceeding to delete all cached folders")
            try:
                for i in appServer.relativeCacheFolders:
                    deleteDirOrFile(module.targetDeploymentPath + scriptGlobals.osDirSeparator + i)
            except OSError: # If directory doesn't exist ignore the raised error
                pass
            
            # Change directory to run the binary from inside the binpath
            pwd = os.getcwd()
            os.chdir(module.targetDeploymentPath + appServer.binPath)
            runProcess("." + scriptGlobals.osDirSeparator + appServer.startCommand)
            os.chdir(pwd)

            # Construct the email notification
            emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)            
            emailRecipients = module.emailNotificationRecipientList
            emailSubject = "Server START: " + module.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
            emailText = startApplicationServerNotificationTemplate(module.name, getCurrentHostname(), guid) 
            
            # Email all required parties
            SendEmail(emailSender, 
                      emailRecipients,
                      emailSubject, 
                      emailText, 
                      scriptGlobals.smtpHost, 
                      scriptGlobals.smtpPort)              
            

        
class GenericApplicationServerKillAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''      
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)
                
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)
        pid = getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier)

        # If process exists...
        if pid:

            # Kill process using pid
            killProcess(pid)
            
            # Construct the email notification
            emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)            
            emailRecipients = module.emailNotificationRecipientList
            emailSubject = "Server KILL: " + module.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
            emailText = killApplicationServerNotificationTemplate(module.name, getCurrentHostname(), guid) 
             
            
            # Email all required parties
            SendEmail(emailSender, 
                      emailRecipients,
                      emailSubject, 
                      emailText, 
                      scriptGlobals.smtpHost, 
                      scriptGlobals.smtpPort)                        


class GenericJBOSSServerStopAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)
        pid = getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier)

        # If process exists...
        if pid:

            # Stop process using pid
            terminateProcess(pid)

            # Construct the email notification
            emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
            emailRecipients = module.emailNotificationRecipientList
            emailSubject = "Server STOP: " + module.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
            emailText = stopApplicationServerNotificationTemplate(module.name, getCurrentHostname(), guid)


            # Email all required parties
            SendEmail(emailSender,
                      emailRecipients,
                      emailSubject,
                      emailText,
                      scriptGlobals.smtpHost,
                      scriptGlobals.smtpPort)


class GenericApplicationServerDelayedRestartAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''      
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)
        
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)
        
        # Construct the email notification
        emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)        
        emailRecipients = module.emailNotificationRecipientList
        emailSubject = "Server RESTART Notification: " + module.name + "@"+ getCurrentHostname()+ " (" + module.friendlyServerName + ")" + " server will restart in " + scriptGlobals.httpServerExecutionTime + " seconds."
        killOperationURL = "http://" + getCurrentHostname() + ":" + str(scriptGlobals.httpServerPort) + "/stopDelayedRestart.foo"
        emailText = restartPendingNotificationTemplate(module.name, getCurrentHostname(), killOperationURL, guid)
        
        # Email all required parties
        SendEmail(emailSender, 
                  emailRecipients,
                  emailSubject,  
                  emailText,
                  scriptGlobals.smtpHost, 
                  scriptGlobals.smtpPort)
        
        # Start timer that will hit the timeout URL when the time ends
        timeoutURL = "http://" + getCurrentHostname() + ":" + str(scriptGlobals.httpServerPort) + "/timeOut.foo"
        timer = Timer(int(scriptGlobals.httpServerExecutionTime), timeoutURL)
        timer.start()
                
        # Expose cancellation URL
        server = launchHTTPServer(int(scriptGlobals.httpServerPort), FireworksHTTPRequestHandler)
        if server.result == 0:
            log.info("Grace period timed-out, proceeding to restart the server...")
            
            # Initialize Stop Action Bundle
            ab = initClassFromStringWithModule(module.moduleStopAB, module)
            log.info("Sleeping for 20 seconds to allow proper server stop...")
            time.sleep(20)
            
            # Initialize Kill Action Bundle (just in case :-))
            ab = initClassFromStringWithModule(module.moduleKillAB, module)
            time.sleep(5) 
                       
            # Initialize Start Action Bundle
            ab = initClassFromStringWithModule(module.moduleStartAB, module)
            
        elif server.result == 1:
            log.info("Cancelled by external client.")
            timer.stop()
            
            # Construct the email notification
            emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, lib.OptParser.options.envprops, scriptGlobals.emailNotificationSenderAddress)            
            emailRecipients = module.emailNotificationRecipientList
            emailSubject = "Server RESTART Cancelled: " + module.name + "@"+ getCurrentHostname()+ " (" + module.friendlyServerName + ")" + " server restart was cancelled"
            killOperationURL = "http://" + getCurrentHostname() + ":" + str(scriptGlobals.httpServerPort) + "/stopDelayedRestart.foo"
            emailText = restartCancellationNotificationTemplate(module.name, getCurrentHostname(), guid) 
             
            
            # Email all required parties
            SendEmail(emailSender, 
                      emailRecipients,
                      emailSubject, 
                      emailText, 
                      scriptGlobals.smtpHost, 
                      scriptGlobals.smtpPort)            
        


class GenericApplicationServerStatusAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)              
        pid = getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier)
        
        if pid: 
            log.info("Process found running from path '" + module.targetDeploymentPath + "' with pid '" + pid + "'.")
        else: 
            log.info("Process running from path '" + module.targetDeploymentPath + "' was not found.")
            

class GenericApplicationServerLogTailAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        logpath = module.relativeLogFilePath % (module.targetDeploymentProfile)
        logExecute("tail -f " + module.targetDeploymentPath + scriptGlobals.osDirSeparator + logpath)


class GenericApplicationServerRollbackAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if Application Server is running
        appServer = ApplicationServer(module, scriptGlobals.appsrvProperties)
        if getProcessPIDByPathAndIdentifier(module.targetDeploymentPath, appServer.processIdentifier): die("The Application Server at '" + module.targetDeploymentPath + "' is up. Rollback will not continue.")

        # Deserialize objects and pass them to executedActionList        
        scriptGlobals.executedActionList = deserializeListFromFile(lib.OptParser.options.rollback)

        # Raise dummy exception
        raise RollbackTriggerException
        


class GenericRollbackAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        guid = generateGUID()
        log.info("Unique ActionBundle execution ID generated: " + guid)

        # Check if server is running
        if getProcessPIDByPath(module.targetDeploymentPath): die("The server at '" + module.targetDeploymentPath + "' is up. Rollback will not continue.")

        # Deserialize objects and pass them to executedActionList
        log.info("Using '" + lib.OptParser.options.rollback + "' to perform Manual Rollback")
        scriptGlobals.executedActionList = deserializeListFromFile(lib.OptParser.options.rollback)

        # Raise dummy exception to enter the Rollback mechanism
        raise RollbackTriggerException

    
class GenericDebugAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        print "Hello World!"

        s = raw_input("")

                
        
                      
        