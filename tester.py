#! /usr/bin/env python
import lib.OptParser as parser
import sys, re, os
from lib.Toolkit import log, logging, readPropertyFromPropertiesFile, scriptGlobals, initClassFromStringWithModule, createDirectoriesRecursively, printOsInformation, checkRequiredExecutablesExist, moveDirOrFile, rollbackActions, die,\
    getAnswerFromUser, produceFinalReport,runOracleScript , appendLineToFileBeforeLine, appendLineToFileAfterLine, removeLineFromFile, extractFileFromZipToDir, extractFileFromCompressedTarToDir, extractCompressedTarToDir, readPropertyFromPropertiesFileWithFallback
from modules.Module import Module
from actions.FileSystemActions import ChangePathPermissions



try: 
    
    # Print OS information
    printOsInformation()
    
    # Check for required executables   
    #checkRequiredExecutablesExist(scriptGlobals.requiredExecutables)
    
    # Initialize working dir
    createDirectoriesRecursively(scriptGlobals.workingDir)
    log.info("Working directory '" + scriptGlobals.workingDir + "'")
    
    # Get Module Properties file
    moduleProperties = extractFileFromZipToDir(parser.options.module, scriptGlobals.modulePropertiesFile, scriptGlobals.workingDir)
    log.info("Module properties file '" + moduleProperties + "'")
    
    # Initialize module to be deployed
    module = Module(parser.options.module, moduleProperties, parser.options.envprops)
       
    # Initialize Module Action Bundle
#    ab = initClassFromStringWithModule(readPropertyFromPropertiesFile("module" + parser.options.action + "AB", scriptGlobals.moduleSectionName, parser.options.modprops), module)

    raw_input("")
#    import code; code.interact(local=locals())

except: 
    raise