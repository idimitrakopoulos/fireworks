#! /usr/bin/env python
import logging
import lib.OptParser as parser
from lib.FileLocker import flock
import sys, re, os, socket, platform, getpass, time, pickle
from lib.Toolkit import log, readPropertyFromPropertiesFile, scriptGlobals, initClassFromStringWithModule, createDirectoriesRecursively, printOsInformation, checkRequiredExecutablesExist, rollbackActions, \
    getAnswerFromUser, produceFinalReport, extractFileFromZipToDir, checkPythonVersion,\
    generateGUID, sendEmail, readPropertyFromPropertiesFileWithFallback,\
    getRoundedTimeDifference, getCurrentHostname, serializeListToFile, scriptGlobals, RollbackTriggerException, initClassFromString, printsScriptInformation, createCustomLogger, acquireLock, dictionaryToString, dateToString, die, isRequiredFileEmpty
from modules.Module import Module
from lib.FunStuff import fireworksAsciiHeader
from notifications.GenericNotificationTemplates import detailedExecutionReportTemplate

try:
    # Acquire Lock
    lock = acquireLock(scriptGlobals.lockFile, True)
    
    # Measure execution time
    startTime = time.time()

    # Print Fireworks execution command
    log.debug("Fireworks execution command '" + " ".join(sys.argv) + "'")

    # Print cool header :-)
    log.info(fireworksAsciiHeader(scriptGlobals.version, scriptGlobals.revision, scriptGlobals.buildDate))

    # Print OS information
    printOsInformation()

    # Generate a unique ActionBundle execution id
    guid = generateGUID()
    log.info("Unique Fireworks Execution ID generated: '" + guid + "'")

    # Initialize working dir
    scriptGlobals.workingDir =  scriptGlobals.workingDir % (parser.options.action, guid)
    
    # Create it
    createDirectoriesRecursively(scriptGlobals.workingDir)
    log.info("Working directory '" + scriptGlobals.workingDir + "'")

    # Start per-execution logger
    log.addHandler(createCustomLogger(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + guid + ".log", scriptGlobals.customLoggingFormat, logging.DEBUG))

    # Get Module Properties file
    isRequiredFileEmpty(parser.options.module)
    moduleProperties = extractFileFromZipToDir(parser.options.module, scriptGlobals.modulePropertiesFile, scriptGlobals.workingDir)
    log.info("Module properties file '" + moduleProperties + "'")
    
    # Initialize module to be deployed
    module = Module(parser.options.module, moduleProperties, parser.options.envprops)

    # Initialize Pre-Execution Logic
    prelogic = initClassFromStringWithModule(module.preExecutionLogicClass, module)

    # Initialize & Execute ActionBundles
    for actionbundleClass in module.actionBundleGroupClasses[parser.options.action]:
        ab = initClassFromStringWithModule(actionbundleClass, module)

    # Initialize Post-Execution Logic
    postlogic = initClassFromStringWithModule(module.postExecutionLogicClass, module)

    #    import code; code.interact(local=locals())
except (Exception, KeyboardInterrupt):

    # Actions for rollback exist and this is not Rollback mode?
    if (len(scriptGlobals.executedActionList) > 0) and (not type(sys.exc_info()[1]) == RollbackTriggerException):
        log.error(str(sys.exc_info()[0]) + " " + str(sys.exc_info()[1])) 
        answer = getAnswerFromUser(str(sys.exc_info()[0]) + " detected. \n\nSelect your action:\n\n(R) Rollback all actions performed so far \n(<any other key>) Show Exception & Quit")
        if (re.compile('^r$', re.I)).match(answer): rollbackActions(scriptGlobals.executedActionList)
        log.debug("Printing initial exception below")
        log.debug("If you think this error is a bug please file it here: https://jira.velti.com/jira40/browse/FW")
        raise
    # Actions for rollback exist and this is Rollback mode?
    elif (len(scriptGlobals.executedActionList) > 0) and (type(sys.exc_info()[1]) == RollbackTriggerException):
        log.info("Manual rollback mode initiated")
        rollbackActions(scriptGlobals.executedActionList)

    # No Actions for rollback exist        
    else:
        log.error(str(sys.exc_info()[0]) + " " + str(sys.exc_info()[1]))
        log.debug("The executed Action list has 0 elements. Nothing to Rollback.")
        log.debug("Printing initial exception below")
        log.debug("If you think this error is a bug please file it here: https://jira.velti.com/jira40/browse/FW")
        raise

else:
    log.info("Printing final report ...")

    # All executed actions are in the executedActionList, use it to print out their report() functions
    produceFinalReport(scriptGlobals.executedActionList)

#finally: # finaly block not supported in Python 2.4 after else: blocks :-(

# Serialize the list queue
fireworksStateFilename = serializeListToFile(scriptGlobals.executedActionList, scriptGlobals.workingDir + scriptGlobals.osDirSeparator + guid + ".fsf")
log.info("Fireworks state file is '" + fireworksStateFilename + "'. You can use this for Rollback operations using the -r switch")
log.info("To perform rollbacks you will need to retain the working directory the script used in this execution '" + scriptGlobals.workingDir + "'")

# Construct the email notification
emailSender = readPropertyFromPropertiesFileWithFallback("emailNotificationSenderAddress", scriptGlobals.scriptVarSectionName, parser.options.envprops, scriptGlobals.emailNotificationSenderAddress)
emailRecipients = scriptGlobals.globalNotificationEmailList
emailSubject = "Fireworks Execution Report: " + module.name + "@"+ getCurrentHostname() + " (" + module.friendlyServerName + ")"
emailText = detailedExecutionReportTemplate(scriptGlobals.version,
                                            scriptGlobals.revision,
                                            scriptGlobals.buildDate,
                                            module.name,
                                            parser.options.action, 
                                            getCurrentHostname(),
                                            scriptGlobals.workingDir,
                                            os.getcwd(), 
                                            guid,
                                            fireworksStateFilename,
                                            " ".join(platform.uname()),
                                            getpass.getuser())
  
# Email all required parties
sendEmail(emailSender, 
          emailRecipients,
          emailSubject, 
          emailText,
          scriptGlobals.smtpHost, 
          scriptGlobals.smtpPort)

# Output execution time
log.debug("Total execution time: " + getRoundedTimeDifference(time.time(), startTime, 2) + "s (includes time spent during user prompts)")

# Salute!
log.info("Bye bye! :-)")