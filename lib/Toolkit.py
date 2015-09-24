# Logging
import exceptions
import logging.config
import os, signal, re, shutil, commands, time, random, socket, smtplib, tarfile, \
    sys, getpass, platform, distutils.dir_util, cPickle
from pickle import dumps, loads
from ConfigParser import ConfigParser, RawConfigParser
from datetime import datetime
from zipfile import ZipFile
from lib.ColorFormatter import ColorFormatter
from random import randint
import lib.OptParser
from lib.FunStuff import finalReportAsciiHeader, dividerAscii, SpinCursor, rollbackAsciiHeader
from lib.FireworksHTTPServer import FireworksHTTPServer
from notifications.GenericNotificationTemplates import constructEmail

class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

def checkFileExists(filename):
    if os.path.isfile(filename):
        return 0
    else:
        return 1

def checkDirExists(path):
    if os.path.isdir(path):
        return 0
    else:
        return 1

class ScriptGlobals(object):
    '''
    classdocs
    '''
    
    globalProperties = "conf/global.properties"
       
    def __init__(self):
        '''
        Constructor
        '''
        # Initialize executedActionList
        self.executedActionList = []

        # Get properties from global.properties
        # [propertyFiles]
        self.logProperties = readPropertyFromPropertiesFile("logProperties", "propertyFiles", self.globalProperties)
        self.appsrvProperties = readPropertyFromPropertiesFile("appsrvProperties", "propertyFiles", self.globalProperties)

        # [moduleProperties]
        self.moduleSectionName = readPropertyFromPropertiesFile("moduleSectionName", "moduleProperties", self.globalProperties)

        # [variousProperties]
        self.workingDir = readPropertyFromPropertiesFile("workingDir", "variousProperties", self.globalProperties)
        self.defaultLogger = readPropertyFromPropertiesFile("defaultLogger", "variousProperties", self.globalProperties)
        self.requiredExecutables = readPropertyFromPropertiesFile("requiredExecutables", "variousProperties", self.globalProperties)
        self.osDirSeparator = readPropertyFromPropertiesFile("osDirSeparator", "variousProperties", self.globalProperties)
        self.oracleLogTemplateFile = readPropertyFromPropertiesFile("oracleLogTemplateFile", "variousProperties", self.globalProperties)        
        self.postgresLogTemplateFile = readPropertyFromPropertiesFile("postgresLogTemplateFile", "variousProperties", self.globalProperties)        
        self.scriptVarSectionName = readPropertyFromPropertiesFile("scriptVarSectionName", "environmentProperties", self.globalProperties)                      
        self.sqlplusLocation = readPropertyFromPropertiesFile("sqlplusLocation", "externalTools", self.globalProperties)
        self.jisqlLocation = readPropertyFromPropertiesFile("jisqlLocation", "externalTools", self.globalProperties)        
        self.cmsStructureImportToolLocation = readPropertyFromPropertiesFile("cmsStructureImportToolLocation", "externalTools", self.globalProperties)        
        self.environmentVariableFile = readPropertyFromPropertiesFile("environmentVariableFile", "variousProperties", self.globalProperties)
        self.modulePropertiesFile = readPropertyFromPropertiesFile("modulePropertiesFile", "moduleProperties", self.globalProperties)
        self.shell = readPropertyFromPropertiesFile("shell", "variousProperties", self.globalProperties)
        self.pythonMajorVersion = readPropertyFromPropertiesFile("pythonMajorVersion", "variousProperties", self.globalProperties)
        self.pythonMinorVersion = readPropertyFromPropertiesFile("pythonMinorVersion", "variousProperties", self.globalProperties)
        self.httpServerPort = readPropertyFromPropertiesFile("httpServerPort", "variousProperties", self.globalProperties)
        self.httpServerExecutionTime = readPropertyFromPropertiesFile("httpServerExecutionTime", "variousProperties", self.globalProperties)
        self.lockFile = readPropertyFromPropertiesFile("lockFile", "variousProperties", self.globalProperties)
        self.manifestFile = readPropertyFromPropertiesFile("manifestFile", "variousProperties", self.globalProperties)
        self.manifestTemplateFile = readPropertyFromPropertiesFile("manifestTemplateFile", "variousProperties", self.globalProperties)

        # [loggingProperties]
        self.customLoggingFormat = readPropertyFromPropertiesFile("customLoggingFormat", "loggingProperties", self.globalProperties)

        # [emailProperties]
        self.emailNotificationSenderAddress = readPropertyFromPropertiesFile("emailNotificationSenderAddress", "emailProperties", self.globalProperties)                
        self.smtpHost = readPropertyFromPropertiesFile("smtpHost", "emailProperties", self.globalProperties)
        self.smtpPort = readPropertyFromPropertiesFile("smtpPort", "emailProperties", self.globalProperties)
        self.globalNotificationEmailList = readPropertyFromPropertiesFile("globalNotificationEmailList", "emailProperties", self.globalProperties).split(",")

        # MANIFEST.MF
        if checkFileExists(self.manifestFile) == 1:
            print "File '" + self.manifestFile + "' does not exist. Sorry, you cannot work with an unreleased version of fireworks. If you must work with it please execute 'cp " + self.manifestTemplateFile + " " +  self.manifestFile +"' and retry running the script."
            sys.exit()
        self.version = readPropertyFromPropertiesFile("version", self.scriptVarSectionName, self.manifestFile)
        self.revision = readPropertyFromPropertiesFile("revision", self.scriptVarSectionName, self.manifestFile)
        self.buildDate = readPropertyFromPropertiesFile("buildDate", self.scriptVarSectionName, self.manifestFile)
        
        self.appendStyleEnum = Enum(["BEFORE", "AFTER"])       
        self.setupEnvironmentVariables()

    def setupEnvironmentVariables(self):
        env = '''IC_INSTALL_DIR=%s
export PATH=$IC_INSTALL_DIR:$PATH
export LD_LIBRARY_PATH=$IC_INSTALL_DIR:$LD_LIBRARY_PATH
        ''' % (os.getcwd() + self.osDirSeparator  + self.sqlplusLocation[0:self.sqlplusLocation.rfind(self.osDirSeparator)])
        
        # Prepare the env var file
        envFile = open(self.environmentVariableFile, 'w')
        envFile.write(env)
        envFile.close()
              

class RollbackTriggerException(exceptions.Exception):
	def __init__(self):
		return

	def __str__(self):
		return "Dummy exception to trigger the Fireworks Rollback mechanism."
        
                 
def logExecute( cmd ):
    log.debug("Shell command '" + cmd + "' will be executed")

    # Check return code
    if os.system(cmd) == 256:
        die("Shell command '" + cmd + "' returned 1")
    else:
        log.info("Shell command '" + cmd + "' was executed")

def logExecuteAndCaptureOutput(cmd):
    log.debug("Shell command '" + cmd + "' will be executed")
    r,w,e = getShell()
    w.write(cmd + "\n")
    w.close()        
    return r, e

def logExecuteAndCheckErrorOutput(cmd, errorMessageList):
    r, e = logExecuteAndCaptureOutput(cmd)
    error = e.read()
    found = False

    for errorMsg in errorMessageList:
        if errorMsg in error:
            log.error(error)

            answer = getAnswerFromUser("The last command executed '" + cmd + " produced an error (see log output above). \n\nSelect your action:\n\n(I) Ignore errors & continue execution \n(<any other key>) Raise error and get the option to rollback (NOTE: Some actions cannot be rolled back): ")
            if (re.compile('^i$', re.I)).match(answer):
                found = True
                pass
                break
            else:
                found = True
                raise Exception

    if not found:
        logIfVerbose(error)

    return r, error  
        
def logExecuteOnEnvReadyShellAndCaptureOutput(cmd):
    log.debug("Shell command '" + cmd + "' will be executed")
    r,w,e = getEnvironmentReadyShell()
    w.write(cmd + "\n")
    w.close()
    log.info("Shell command '" + cmd + "' was executed")
    return r, w, e


        
def logIfVerbose( msg ):
    if lib.OptParser.options.verbose == 2: log.debug(msg)
        
    
def die(msg="Error"):
    log.critical(msg)
    sys.exit()

def rmTreeOnError(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.
    
    Usage : ``shutil.rmtree(path, rmTreeOnError=rmTreeOnError)``
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        pass
    
def deleteDirOrFile(path):
    logIfVerbose("rm -rf " + path)
    if os.path.isdir(path):    
        shutil.rmtree(path, onerror=rmTreeOnError)
    else:
        os.remove(path)
        

def copyDirOrFile(src, dst):
    logIfVerbose("cp -a " + src + " " + dst)
    if os.path.isfile(src):
        if not os.path.isdir(dst[0:dst.rfind(scriptGlobals.osDirSeparator)]): createDirectoriesRecursively(dst[0:dst.rfind(scriptGlobals.osDirSeparator)])
        os.system("touch " + dst)
        shutil.copy(src, dst)
    else:
        if not os.path.isdir(dst[0:dst.rfind(scriptGlobals.osDirSeparator)]): createDirectoriesRecursively(dst[0:dst.rfind(scriptGlobals.osDirSeparator)])
        if os.path.isdir(dst):
            # Delete already existing file/folder because otherwise it will not allow you to overwrite
            log.debug(dst + " already exists, overwriting ...")
            deleteDirOrFile(dst)
        shutil.copytree(src, dst)

        
def copyDirOrFile2(src, dst):
    logIfVerbose("cp -a " + src + " " + dst)
    if os.path.isfile(src):
        if not os.path.isdir(dst[0:dst.rfind(scriptGlobals.osDirSeparator)]): createDirectoriesRecursively(dst[0:dst.rfind(scriptGlobals.osDirSeparator)])
        os.system("touch " + dst)
        shutil.copy(src, dst)
    elif os.path.isdir(src):
        if not os.path.isdir(dst[0:dst.rfind(scriptGlobals.osDirSeparator)]): createDirectoriesRecursively(dst[0:dst.rfind(scriptGlobals.osDirSeparator)])
        distutils.dir_util.copy_tree(src, dst)
    else: # Ticket: FW-5
        log.warn("Couldn't copy '" + src + "' to '" + dst +"'. Source '"+ src + "' isn't a valid file or directory.")


def deleteListOfDirsOrFiles(deleteFromPath, PathToTakeListOfFilesAndDirs):
    log.info("Attempting to delete files/dirs that exist inside " + PathToTakeListOfFilesAndDirs + " from " + deleteFromPath)
    # Take list of files/dirs    
    for root, dirs, files in os.walk(PathToTakeListOfFilesAndDirs, topdown=False):
        # change root
        root = deleteFromPath
        # Delete files
        for name in files:
            log.debug("Deleting file '" + root + scriptGlobals.osDirSeparator + name + "'")
            os.remove(os.path.join(root, name))
        # Delete dirs if empty
        for name in dirs:
            if os.listdir(name) == []:
                log.debug("Directory '" + root + scriptGlobals.osDirSeparator + name + "' is empty. Removing it.")
                os.rmdir(os.path.join(root, name))

def moveDirOrFile(src, dst):
    logIfVerbose("mv " + src + " " + dst)
    if os.path.isfile(src):
        if not os.path.isdir(dst[0:dst.rfind(scriptGlobals.osDirSeparator)]): 
            createDirectoriesRecursively(dst[0:dst.rfind(scriptGlobals.osDirSeparator)])        
    shutil.move(src, dst)    
    
def changePathOwnership(path, uid, gid):
    logIfVerbose("chown " + path + " " + str(uid)  + ":" +  str(gid))  
    os.chown(path, uid, gid)   
    for root, dirs, files in os.walk(path):  
        for item in dirs:  
            os.chown(os.path.join(root, item), uid, gid)
        for item in files:
            os.chown(os.path.join(root, item), uid, gid) 

def changePathPermissions(path, mode):
    logIfVerbose("chmod -R " + str(mode) + " " + path)
    os.chmod(path, mode)

    # If path is directory recursively change all permissions on contained files too.
    if (os.path.isdir(path)):
        for i in os.listdir(path):
            logIfVerbose("chmod -R " + str(mode) + " " + path + scriptGlobals.osDirSeparator + i)
            os.chmod(path + scriptGlobals.osDirSeparator + i, mode)

def getPathPermissions(path):
    return os.stat(path).st_mode & 0777   

def readPropertyFromPropertiesFile(propertyName, propertiesSectionName, propertiesFilename, warnIfEmpty = True):
    result = ""
    if (os.path.isfile(propertiesFilename)):
        try:
            cfg = RawConfigParser()
            cfg.read(propertiesFilename)
            result = cfg.get(propertiesSectionName, propertyName)
            if (globals().has_key('log')):
                logIfVerbose("Value of '" + propertyName +"' from '[" + propertiesSectionName +"]' in '" + propertiesFilename + "' = '" + result + "'")
                if result == "" and warnIfEmpty:
                    log.warn("No value exists for '" + propertyName + "' on section '[" + propertiesSectionName + "]' inside file '" + propertiesFilename + "'")
                elif result == "" and not warnIfEmpty:
                    log.info("No value exists for '" + propertyName + "' on section '[" + propertiesSectionName + "]' inside file '" + propertiesFilename + "' however empty values for this property are expected and some times intentional.")
        except:
            raise
    else:
        if (globals().has_key('log')):
            logIfVerbose("Properties file '" + propertiesFilename + "' does not exist.")
        result = None
        
    return result 

def readPropertyFromPropertiesFileWithFallback(propertyName, propertiesSectionName, propertiesFilename, fallbackValue):
    result = ""
    try:
        result = readPropertyFromPropertiesFile(propertyName, propertiesSectionName, propertiesFilename)
    except:
        log.info("Property '" + propertyName +"' from '" + propertiesSectionName +"' in '" + propertiesFilename + "' doesn't exist, falling back to '" + fallbackValue + "'")
        result = fallbackValue
        
    return result


def readAllPropertiesFromPropertiesFile(propertiesSectionName, propertiesFilename):
    log.debug("Attempting to read all properties from '" + propertiesSectionName +"' in '" + propertiesFilename + "'")
    cfg = ConfigParser()
    cfg.read(propertiesFilename)
    return cfg.options(propertiesSectionName)

def stringToDictionary(string):
    logIfVerbose("Attempting to turn string '" + string + "' into dictionary")
    result = loads(string)
    return result 

def dictionaryToString(dictionary):
    result = dumps(dictionary)
    return result 

def getClass( kls ):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m

def initClassFromString(fullClassName):
    log.debug("Instantiating '" + fullClassName + "'")
    stub = getClass(fullClassName)
    return stub()

def initModuleClassFromString(fullClassName, moduleFilename, modulePropertiesFilename, environmentPropertiesFilename):
    log.debug("Instantiating Module subclass '" + fullClassName + "'")
    stub = getClass(fullClassName)
    return stub(moduleFilename, modulePropertiesFilename, environmentPropertiesFilename)    

def initClassFromStringWithModule(fullClassName, module):
    log.debug("Instantiating class '" + fullClassName + "' with module '" + module.name + "'")
    stub = getClass(fullClassName)
    return stub(module)

def findFiletype(filename):
    log.debug("Filetype for filename '" + filename + "' is " + filename.split(".")[-1])
    return filename[filename.find(".")+1:len(filename)]

def dateToString():
    dt = datetime.now()
    return dt.strftime("%Y%m%d%I%M%S")

def createDirectoriesRecursively(pathToCreate):
    log.debug("Attempting to create directories '" + pathToCreate + "' recursively")
    if not os.access(pathToCreate, os.F_OK):
        try:    
            os.makedirs(pathToCreate)
        except Exception:
            log.error("Failed to create directories '" + pathToCreate + "' recursively")
            raise Exception
    else:
        log.debug("Path already exists '" + pathToCreate + "'")
        
    return pathToCreate

def removeDirectoriesRecursively(pathToRemove):
    result = False
    log.debug("Attempting to remove directories '" + pathToRemove + "' recursively")
    if os.path.isdir(pathToRemove):
        try:
            os.removedirs(pathToRemove)
            result = True
        except Exception:
            log.error("Failed to remove leaf directory '" + pathToRemove + "' and hence its parent directories recursively. Check if its empty.")
    else:
        log.debug("Path doesn't exist '" + pathToRemove + "'")
        
    return result


def createDirectory(pathToCreate):
    log.debug("Attempting to create directory '" + pathToCreate + "'")
    if not os.access(pathToCreate, os.F_OK):
        try:
            os.mkdir(pathToCreate)
        except Exception:
            log.error("Failed to create directory '" + pathToCreate + "'")
            raise Exception
    else:
        log.debug("Path already exists '" + pathToCreate + "'")

    return pathToCreate

def removeDirectory(pathToRemove):
    result = False
    log.debug("Attempting to remove directory '" + pathToRemove + "'")
    if os.path.isdir(pathToRemove):
        try:
            os.rmdir(pathToRemove)
            result = True
        except Exception:
            log.error("Failed to remove directory '" + pathToRemove + "'. Check if its empty.")
    else:
        log.debug("Path doesn't exist '" + pathToRemove + "'")

    return result

def generateRandomDirectoryUnderPath(path):
    randomResult = generateGUID()
    log.debug("Random folder generated '" + path + scriptGlobals.osDirSeparator + randomResult + "'")
    return path + scriptGlobals.osDirSeparator + randomResult

  
def replaceInsensitiveStringInFile(stext, rtext, templateFilename):
    try:
        input = open(templateFilename).readlines()
        output = open(templateFilename, 'w')
        lineCount = 1
        occurences = 0
                                   
        log.debug("Searching for string '" + stext + "' in '" + templateFilename + "'")
        
        for line in input:           
            try:
                fa = re.findall(re.escape(stext), line, re.IGNORECASE)[0]                
                repline = line.replace(fa, rtext)
                log.debug("String '" + stext + "' successfully replaced with '" + rtext + "' on line " + `lineCount` + " of file '" + templateFilename + "'")                
                output.write(repline)
                lineCount +=1
                occurences +=1
            except:
#                logIfVerbose("String '" + stext + "' was not found in '" + templateFilename + "' on line " + `lineCount` + " '" + line + "'")
                output.write(line)
                lineCount +=1

           
        output.close()
        if ( occurences > 0 ) : log.debug("String '" + stext + "' was replaced " + `occurences` + " time(s) with '" + rtext + "' in file '" + templateFilename + "'")
    except Exception:
        raise    
    


def replaceStringsInFileUsingAnotherFile(propertiesSectionName, inputFilename, templateFilename):
        availableProperties = readAllPropertiesFromPropertiesFile(propertiesSectionName, inputFilename)
        for p in availableProperties:
            value = readPropertyFromPropertiesFile(p, propertiesSectionName, inputFilename)
#            log.debug("Replacing property '" + p + "' with value '" + value + "' inside file '" + templateFilename + "'.")
            replaceInsensitiveStringInFile("${"+p+"}", value, templateFilename)
        
def beginBusyIndicatorThread(msg):
    spin = SpinCursor(msg) 
    spin.start()
    return spin

def endBusyIndicatorThread(busyIndicator):
    busyIndicator.stop()
    
def extractZipToDir(zipFilename, location):
    log.debug("Extracting '" + zipFilename +"' to '" + location + "'" )
    
#    bit = beginBusyIndicatorThread("")
    
    if not location[len(location)-1] == scriptGlobals.osDirSeparator: 
        location = location + scriptGlobals.osDirSeparator
            
    z = ZipFile(zipFilename)
    for f in z.namelist():
        if f.endswith('/'):
            if not os.path.isdir(location + f): os.makedirs(location + f)
        else:
            log.debug("> " + f)
            lastDirSeparatorIndex=f.rfind(scriptGlobals.osDirSeparator)
            if lastDirSeparatorIndex > -1 :
                extractFileFromZipToDir(zipFilename, f, location + f[0:lastDirSeparatorIndex])
            else:
                extractFileFromZipToDir(zipFilename, f, location)
    
#    bit.stop()
    
def extractFileFromZipToDir(zipFilename, filenameToExtract, location):
    log.debug("Extracting '" + filenameToExtract +"' from '" + zipFilename + "' to '" +  location + "'")    
    if not location[len(location)-1] == scriptGlobals.osDirSeparator: 
        location = location + scriptGlobals.osDirSeparator
        if not os.path.isdir(location): os.makedirs(location)
        
    zf = ZipFile(zipFilename, 'r')
    f = location + filenameToExtract[filenameToExtract.rfind(scriptGlobals.osDirSeparator)+1:len(filenameToExtract)]
    outputFile = open(f, 'wb')
    outputFile.write(zf.read(filenameToExtract))
    outputFile.close()
    return f      

        
#def extractZipToDir(zipFilename, location):
#    log.debug("Extracting '" + zipFilename +"' to '" + location + "'" )        
#    z = ZipFile(zipFilename)            
#    z.extractall(location)
        
#def extractFileFromZipToDir(zipFilename, filenameToExtract, location):
#    log.debug("Extracting '" + filenameToExtract +"' from '" + zipFilename +"' to '" + location + "'" )    
#    z = ZipFile(zipFilename)            
#    z.extract(filenameToExtract, location)


def extractCompressedTarToDir(compressedFilename, compressionType, location):
    import tarfile
    
    log.debug("Extracting '" + compressedFilename +"' to '" + location + "'" )
    
    tar = tarfile.open(compressedFilename,compressionType)
    fileList = tar.getnames()
    for fileName in fileList:        # Filenames
        xfile = tar.extractfile(fileName)
        if xfile:  # True if data file, False if directory (apparently)
            extractFileFromCompressedTarToDir(fileName, compressedFilename, compressionType, location + scriptGlobals.osDirSeparator + fileName[0:fileName.rfind(scriptGlobals.osDirSeparator)])
        else:                       # ASSuME xfile None because filename is a directory
            try:
                os.mkdir(location + scriptGlobals.osDirSeparator + fileName)        # Also ASSuME higher directories show up first
            except Exception, e:
                if e[0] == 183:     # This happens when you try to re-make an existing directory
                    continue        # Ignore duplicate directory
                else:
                    print repr(e)
                    raise Exception, e
    tar.close()    

def extractFileFromCompressedTarToDir(filenameToExtract, compressedFilename, compressionType, location):
    log.debug("Extracting '" + filenameToExtract +"' from '" + compressedFilename + "' to '" +  location + "'")
    
    tar = tarfile.open(compressedFilename, compressionType)
    x = tar.extractfile(filenameToExtract)
    data = x.read()
    f = location + scriptGlobals.osDirSeparator + filenameToExtract[filenameToExtract.rfind(scriptGlobals.osDirSeparator)+1:len(filenameToExtract)]            
    fo = open(f, "wb")
    fo.write(data)
    fo.close()                         
    tar.close() 
    
#def extract_from_zip(zipFilename, filenameToExtract, location):
#    self.path[self.path.rfind(scriptGlobals.osDirSeparator)+1:len(self.path)]
#    zipFilename = ZipFile(zipFilename, 'r')
#    outputFile = open(filenameToExtract, 'wb')
#    outputFile.write(zipFilename.read(location))
#    outputFile.close()    
                

def raiseNotImplementedException():
    raise NotImplementedError, "Oops! This part of the functionality has not been implemented ... Bye bye!"

def grepFile(stext, filename):
    log.debug("Searching for '" + stext + "' in '" + filename + "'.")
    result = None
    try:
        input = open(filename).readlines()                                
        log.debug("Searching for string '" + stext + "' in '" + filename + "'")
        
        for line in input:
            m = re.search(stext, line)
            try:
                if m.group(0) != None:         
                    result = line
            except Exception:
                pass             
    except Exception:
        raise   
    
    return result

def getCorrectAnswerFromUser(question, correctAnswer):
    log.info(question)
    s = raw_input("")
    if s != correctAnswer:
        die("User gave a wrong response '" + s + "' to the question '" + question + "'. Accepted answer is '" + correctAnswer + "'.")

def getAnswerFromUser(question, doConfirmation = True):
    log.info(question)
    reply = raw_input("> ")
    log.info("User replied: '" + reply + "'")
    if doConfirmation:
        a = getAnswerFromUser("You replied '" + reply + "'\n\nAre you sure?\n\n(Y) Yes (<any other key>) No", False)
        if not (re.compile('^y$', re.I)).match(a):
            reply = getAnswerFromUser(question, True)
           
    return reply

def runProcess(command):
    log.info("Running process '" + command + " &'")
    os.system(command + " &")
    
def getProcessPIDByPath(processPath):
    for line in os.popen("ps x"):
        fields = line.split()
        
        if line.find(processPath) > 0:
            log.info("Process found '" + line + "'")
            
            return fields[0]
                
    # else
    log.info("Process pid running from path '" + processPath + "' was not found.")
    
def getProcessPIDByPathAndIdentifier(processPath, processIdentifier):
    for line in os.popen("ps x"):
        fields = line.split()
        
        if (processPath in line) and (processIdentifier in line):
            log.info("Process found '" + line + "'")
            
            return fields[0]

def getProcessPIDByIdentifier(processIdentifier):
    for line in os.popen("ps x"):
        fields = line.split()

        if (processIdentifier in line):
            log.info("Process found '" + line + "'")

            return fields[0]
                
    # else
    log.info("Process pid running from identifier '" + processIdentifier + "' was not found.")

def killProcess(pid):
    logIfVerbose("kill -9 " + pid)
    os.kill(int(pid), signal.SIGKILL)

def terminateProcess(pid):
    logIfVerbose("kill " + pid)
    os.kill(int(pid), signal.SIGTERM)
    
def executableExists(executable):
    log.info("Checking '" + executable + "' if exists")
    status, output = commands.getstatusoutput(executable)
    log.info(status)
    return status
    

def checkRequiredExecutablesExist(commaSeparatedExecutablesString):
    for executable in commaSeparatedExecutablesString.split(","):
        log.debug("Checking for '" + executable + "' executable existence locally")
        result = which(executable)
        if (result == None):
            die("Required executable '" + executable + "' wasn't found locally")
        else:
            log.info("Required executable '" + executable + "' was found locally")

def checkUserIsRoot(user):
    return user == "root"

def which(program):
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def runOracleScriptFromFile(scriptFilename, connectionString):
    log.info("Executing '" + scriptFilename + "' on '" + connectionString + "'. This may take some time, please be patient...")
    
#    bit = beginBusyIndicatorThread("")
    
    r,w,e = logExecuteOnEnvReadyShellAndCaptureOutput(os.getcwd() + scriptGlobals.osDirSeparator + scriptGlobals.sqlplusLocation + " \"" + connectionString + "\" @" + scriptFilename)
    
    output = r.read()
    error = e.read()

#    bit.stop()
        
    if (error): 
        log.critical(error)
        raise Exception    
        
    if (output.find("ORA-") > 0) or (output.find("SP2-") > 0) or (output.find("Errors:") > 0)  or (output.find("Warning:") > 0):
        log.error(output)
        
        answer = getAnswerFromUser("The last script executed '" + scriptFilename +"' on '" + connectionString + " produced an error (see log output above). \n\nSelect your action:\n\n(I) Ignore errors & continue script execution \n(<any other key>) Raise error and get the option to rollback (NOTE: SQL actions cannot be rolled back): ")
        if (re.compile('^i$', re.I)).match(answer): pass
        else: 
            raise Exception
    else:
        logIfVerbose(output)

    return output

def runOracleScript(scriptText, connectionString, doCommit=False, headersOff=False):
    log.info("Executing '" + scriptText + "' on '" + connectionString + "'. This may take some time, please be patient...")
    
#    bit = beginBusyIndicatorThread("")
    
    # Commit whatever is in scriptText
    commit = ""
    if doCommit: commit = "commit;"

    # Remove headers of table in results 
    heaoff = "set hea off"    
    if headersOff: heaoff = "set hea off;"
     
    s = '''%s -s '%s' << EOF
%s
%s
%s
EOF
    ''' % (os.getcwd() + scriptGlobals.osDirSeparator + scriptGlobals.sqlplusLocation, connectionString, heaoff, scriptText, commit)  
    r,w,e = logExecuteOnEnvReadyShellAndCaptureOutput(s)
    
    output = r.read()
    error = e.read()
    
#    bit.stop()
    
    if (error): 
        log.critical(error)
        raise Exception    
    

    
    if (output.find("ORA-") > 0) or (output.find("SP2-") > 0) or (output.find("Errors:") > 0)  or (output.find("Warning:") > 0):
        log.error(output)
        
        answer = getAnswerFromUser("The last script executed '" + scriptText +"' on '" + connectionString + " produced an error (see log output above). \n\nSelect your action:\n\n(I) Ignore errors & continue script execution \n(<any other key>) Raise error and get the option to rollback (NOTE: SQL actions cannot be rolled back): ")
        if (re.compile('^i$', re.I)).match(answer): pass
        else: 
            raise Exception
    else:
        logIfVerbose(output)
    
    return output    

def runPostgresScriptFromFile(scriptFilename, username, password, connectionString):
    log.info("Executing '" + scriptFilename + "' on '" + username + "/" + password + "' '" + connectionString + "'. This may take some time, please be patient...")
    
    # java -cp /home/idimitrakopoulos/dev/projects/fireworks/trunk/src/ext-tools/jisql-2.0.8/:/home/idimitrakopoulos/dev/projects/fireworks/trunk/src/ext-tools/jisql-2.0.8/lib/jisql-2.0.8.jar:/home/idimitrakopoulos/dev/projects/fireworks/trunk/src/ext-tools/jisql-2.0.8/lib/postgresql-9.0-801.jdbc4.jar com.xigole.util.sql.Jisql -user mms -password mms -driver postgresql -cstring jdbc:postgresql://10.1.2.88:5432/json -c \;
    # http://www.xigole.com/software/jisql/jisql.jsp
    
#    bit = beginBusyIndicatorThread("")
    
    if log.level == logging.DEBUG: 
        debugFlag = "-debug"
    else:
        debugFlag = ""    
    
    command = '''
    java -cp %s:%s:%s com.xigole.util.sql.Jisql %s -user '%s' -password '%s' -driver postgresql -cstring %s -input %s -c \;
    ''' % (os.getcwd() + scriptGlobals.osDirSeparator + scriptGlobals.jisqlLocation, 
           os.getcwd() + scriptGlobals.osDirSeparator + scriptGlobals.jisqlLocation + scriptGlobals.osDirSeparator + "lib" + scriptGlobals.osDirSeparator + "jisql-2.0.8.jar",
           os.getcwd() + scriptGlobals.osDirSeparator + scriptGlobals.jisqlLocation + scriptGlobals.osDirSeparator + "lib" + scriptGlobals.osDirSeparator + "postgresql-9.0-801.jdbc4.jar",
           debugFlag,
           username,
           password,
           connectionString,
           scriptFilename)
    
    r,w,e = logExecuteOnEnvReadyShellAndCaptureOutput(command)
    
    output = r.read()
    error = e.read()

#    bit.stop()
    
    if ("SQLException" in error):
        log.error(error)
        
        answer = getAnswerFromUser("The last script executed '" + scriptFilename + "' on '" + username + "/" + password + "' '" + connectionString + " produced an error (see log output above). \n\nSelect your action:\n\n(I) Ignore errors & continue script execution \n(<any other key>) Raise error and get the option to rollback (NOTE: SQL actions cannot be rolled back): ")
        if (re.compile('^i$', re.I)).match(answer): pass
        else: 
            raise Exception        
    elif (error):
        log.critical(error)
        raise Exception           
    
    logIfVerbose(output)

    return output        


def runPostgresScript(script, username, password, connectionString):
    log.info("Executing '" + script + "' on '" + username + "/" + password + "' '" + connectionString + "'. This may take some time, please be patient...")
    
    # java -cp /home/idimitrakopoulos/dev/projects/fireworks/trunk/src/ext-tools/jisql-2.0.8/:/home/idimitrakopoulos/dev/projects/fireworks/trunk/src/ext-tools/jisql-2.0.8/lib/jisql-2.0.8.jar:/home/idimitrakopoulos/dev/projects/fireworks/trunk/src/ext-tools/jisql-2.0.8/lib/postgresql-9.0-801.jdbc4.jar com.xigole.util.sql.Jisql -user mms -password mms -driver postgresql -cstring jdbc:postgresql://10.1.2.88:5432/json -c \;
    # http://www.xigole.com/software/jisql/jisql.jsp
        
#    bit = beginBusyIndicatorThread("")
    
    if log.level == logging.DEBUG: 
        debugFlag = "-debug"
    else:
        debugFlag = ""
    
    command = '''
    java -cp %s:%s:%s com.xigole.util.sql.Jisql %s -user '%s' -password '%s' -driver postgresql -cstring %s -query "%s" -c \;
    ''' % (os.getcwd() + scriptGlobals.osDirSeparator + scriptGlobals.jisqlLocation, 
           os.getcwd() + scriptGlobals.osDirSeparator + scriptGlobals.jisqlLocation + scriptGlobals.osDirSeparator + "lib" + scriptGlobals.osDirSeparator + "jisql-2.0.8.jar",
           os.getcwd() + scriptGlobals.osDirSeparator + scriptGlobals.jisqlLocation + scriptGlobals.osDirSeparator + "lib" + scriptGlobals.osDirSeparator + "postgresql-9.0-801.jdbc4.jar",
           debugFlag,           
           username,
           password,
           connectionString,
           script)
    
    r,w,e = logExecuteOnEnvReadyShellAndCaptureOutput(command)
    
    output = r.read()
    error = e.read()

#    bit.stop()
        
    if ("SQLException" in error):
        log.error(error)
        
        answer = getAnswerFromUser("The last script executed '" + script + "' on '" + username + "/" + password + "' '" + connectionString + " produced an error (see log output above). \n\nSelect your action:\n\n(I) Ignore errors & continue script execution \n(<any other key>) Raise error and get the option to rollback (NOTE: SQL actions cannot be rolled back): ")
        if (re.compile('^i$', re.I)).match(answer): pass
        else: 
            raise Exception        
    elif (error):
        log.critical(error)
        raise Exception           
    
    logIfVerbose(output)

    return output    

def printOsInformation():
    log.info("Script running on '" + " ".join(platform.uname()) + "' from within '" + os.getcwd() +"' by user '" + getpass.getuser() + "'" )

def printsScriptInformation():
    log.info("Fireworks Script version  '" + scriptGlobals.version + "  r" + scriptGlobals.revision +"' built on '" + scriptGlobals.buildDate + "'" )

def checkRequiredPathVariables():
    log.info("Checking if the $PATH environment variable is properly set ...")    
    if os.getenv("PATH").find(os.getcwd() + scriptGlobals.osDirSeparator  + scriptGlobals.sqlplusLocation[0:scriptGlobals.sqlplusLocation.rfind(scriptGlobals.osDirSeparator)]) == -1:
        die("Your path is set incorrectly. Please run  \". " + scriptGlobals.environmentVariableFile +"\"")    

def getEnvironmentReadyShell():
    import popen2
    r,w,e = popen2.popen3(scriptGlobals.shell)
    w.write(". " + os.getcwd() + scriptGlobals.osDirSeparator + scriptGlobals.environmentVariableFile + "\n")
    return r, w, e

def getShell():
    import popen2
    r,w,e = popen2.popen3(scriptGlobals.shell)
    return r, w, e
    
def rollbackActions(rollbackQueue):
    log.info(rollbackAsciiHeader())    
    log.info("Rollback operation initiated. Actions in rollback queue: " + str(len(rollbackQueue)))
    
    # While there are still actions to rollback
    while len(rollbackQueue) != 0:
        # Remove last item from the list
        action = rollbackQueue.pop()
        log.debug("Processing action '" + action.__class__.__name__ + "' " + str(action.__dict__) )
        # Execute the action rollback
        action.undoSuper()
    
    log.info("Rollback operation complete")
    
def sprintfOnDictionaryValues(dictionary, string):
        for k,v in dictionary.items():
            logIfVerbose(k + ":" + v + " = " + string)
            try:
                dictionary[k] = v % (string)    
            except TypeError:
                pass

def sprintfOnListValues(list, string):
    try:
        for index, item in enumerate(list):
            newItem = item % (string)      
            logIfVerbose(item + " = " + newItem)  
            list[index] = newItem
    except TypeError:
        pass
    return list      
        
def produceFinalReport(actionStack):
    if len(actionStack) > 0:
            log.info(finalReportAsciiHeader())
            for action in actionStack:
                action.report()
            log.info(dividerAscii())
        
    
def exportPathVariable(valueToExport):
    os.environ['PATH'] = os.getenv('PATH') + ':' + valueToExport
    
def appendStringToEOF(s, filename):
    logExecute("echo '" + s +"' >> " + filename)

def appendRequiredStringsToOracleSQLFile(filename):
    appendStringToEOF("", filename)
    appendStringToEOF("/", filename) # force Oracle to produce an error if any unclosed blocks are in the end of the file
    appendStringToEOF("commit;", filename)
    appendStringToEOF("quit;", filename)


def generateGUID( *args ):
    """
    Generates a universally unique ID.
    Any arguments only create more randomness.
    """
    t = long( time.time() * 1000 )
    r = long( random.random()*100000000000000000L )
    try:
        a = getCurrentHostname()
    except:
        # if we can't get a network address, just imagine one
        a = random.random()*100000000000000000L
    
    data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
    import md5 # deprecated annoying library for python >2.4
    data = md5.md5(data).hexdigest()
    return data


def appendLineToFileAfterLine(lineToFind, lineToAppend, fileName, tmpFileName):
    f = open(fileName)
    nf = open(tmpFileName, 'w')
    found = False
    
    log.debug("Attempting to append line '" + lineToAppend +"' after any line '" + lineToFind + "' on file '" + fileName + "'")
    
    for line in f:
        print line
        nf.writelines(line)
        if line == lineToFind + "\n":
            nf.writelines(lineToAppend)
            log.debug("Line '" + lineToAppend +"' appended after '" + lineToFind + "' on file '" + fileName + "'")            
            found = True
    
    if not found: log.error("Line '" + lineToFind +"' was not found on file '" + fileName +"' ")
    
    f.close()
    nf.close()
    
    moveDirOrFile(tmpFileName, fileName)
    return fileName                

def appendLineToFileBeforeLine(lineToFind, lineToAppend, fileName, tmpFileName):
    f = open(fileName)
    nf = open(tmpFileName, 'w')
    found = False
    
    log.debug("Attempting to append line '" + lineToAppend +"' before any line '" + lineToFind + "' on file '" + fileName + "'")    
    
    for line in f:
        if line == lineToFind + "\n":
            nf.writelines(lineToAppend)
            log.debug("Line '" + lineToAppend +"' appended before '" + lineToFind + "' on file '" + fileName + "'")            
            found = True            
            
        nf.writelines(line)

    if not found: log.error("Line '" + lineToFind +"' was not found on file '" + fileName +"' ")
            
    f.close()
    nf.close()
    
    moveDirOrFile(tmpFileName, fileName)
    return fileName

def removeLineFromFile(lineToFind, fileName, tmpFileName):
    f = open(fileName)
    nf = open(tmpFileName, 'w')
    found = False
    
    log.debug("Attempting to remove line '" + lineToFind + "' from file '" + fileName + "'")    
    
    for line in f:
        if line == lineToFind + "\n":
            log.debug("Line '" + lineToFind +"' removed from file '" + fileName + "'")            
            found = True                        
            pass
        else:
            nf.writelines(line)            


    if not found: log.error("Line '" + lineToFind +"' was not found on file '" + fileName +"' ")
            
    f.close()
    nf.close()
    
    moveDirOrFile(tmpFileName, fileName)
    return fileName

def getDirectoryRecursiveSize(dir):
    total_size = os.path.getsize(dir)
    for item in os.listdir(dir):
        itempath = os.path.join(dir, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += getDirectoryRecursiveSize(itempath)
    return total_size

def addCronJob(cronLine):
    logExecute("crontab -l | { cat; echo '" + cronLine + "'; } | crontab -")

def sendEmail(sender, receivers, subject, message, smtpServer, smtpPort):
    if not lib.OptParser.options.silent:
        email = constructEmail(sender, 
                    receivers, 
                    subject, 
                    message)
        try:
            
            smtpObj = smtplib.SMTP(smtpServer, smtpPort)
            smtpObj.sendmail(sender, receivers, email)
            
        except:
            log.info("Unable to send email from '" + sender + "' to '" + ",".join(receivers) + "' via '" + smtpServer + ":" + smtpPort + "'")
            pass  


def checkUrlExists(url):
    import httplib
    from httplib import HTTP
    from urlparse import urlparse
    
    log.debug("Checking if '" + url + "' is a URL")
    try: 
        p = urlparse(url)
        h = HTTP(p[1])
        h.putrequest('HEAD', p[2])
        h.endheaders()
        log.info("String '" + url + "' is a URL")
                
#        return h.getreply()[0] == httplib.OK
        return True
    except Exception:
        log.debug("String '" + url + "' isn't a URL")        
        return False
        
def url2name(url):
    from os.path import basename
    from urlparse import urlsplit
    return basename(urlsplit(url)[2])

def downloadFile(url, localDirectory):
    import urllib2
    
    localName = url2name(url)
    req = urllib2.Request(url)
    r = urllib2.urlopen(req)
    if r.info().has_key('Content-Disposition'):
        # If the response has Content-Disposition, we take file name from it
        localName = r.info()['Content-Disposition'].split('filename=')[1]
        if localName[0] == '"' or localName[0] == "'":
            localName = localName[1:-1]
    elif r.url != url: 
        # if we were redirected, the real file name we take from the final URL
        localName = url2name(r.url)
    
    createDirectoriesRecursively(localDirectory)
    
    log.info("Downloading file '" + url + "' into '" + localDirectory + "'. Please wait ...")
    f = open(localDirectory + scriptGlobals.osDirSeparator + localName, 'wb')
    f.write(r.read())
    f.close()
    
    return localDirectory + scriptGlobals.osDirSeparator + localName

#def svnCheckout(svnUrl, pathToCheckout):
#    import svn.core
#    import svn.client
#    pool = svn.core.svn_pool_create(None)
#    svn.core.svn_config_ensure( None, pool )
#    ctx = svn.client.svn_client_ctx_t()
#    config = svn.core.svn_config_get_config( None, pool )
#    ctx.config = config
#    rev = svn.core.svn_opt_revision_t()
#    rev.kind = svn.core.svn_opt_revision_head
#    rev.number = 0
#    ctx.auth_baton = svn.core.svn_auth_open( [], pool )
#    svn.client.svn_client_checkout(svnUrl, pathToCheckout, rev, 0, ctx, pool)    

        
def checkPythonVersion(testedMajorVersion, testedMinorVersion):   
    logIfVerbose("The current Fireworks version you are running is tested with Python " + testedMajorVersion + "." + testedMinorVersion + ".x")
    
    currentMajorVersion = sys.version_info[0]
    currentMinorVersion = sys.version_info[1]
    
    if (str(currentMajorVersion) == str(testedMajorVersion) and str(currentMinorVersion) == str(testedMinorVersion)):
        log.info("This system currently runs Python '" + sys.version + "' which is the same version this script was written for.")       
    elif (lib.OptParser.options.compatibility == True) and (str(currentMajorVersion) != str(testedMajorVersion) or str(currentMinorVersion) != str(testedMinorVersion)):
        log.warn("This system currently runs Python '" + sys.version + "' but the script was written for Python " + testedMajorVersion + "." + testedMinorVersion + ".x. The user has chosen to override this warning.")
    elif (lib.OptParser.options.compatibility == False) and (str(currentMajorVersion) != str(testedMajorVersion) or str(currentMinorVersion) != str(testedMinorVersion)):
        die("This system currently runs Python '" + sys.version + "' but the script was written for Python " + testedMajorVersion + "." + testedMinorVersion + ".x. If you want to override this please use the compatibility switch (-c) but be prepared for possible problems.")

def isPythonVersion(majorVersion, minorVersion):
    return (majorVersion == sys.version_info[0]) and (minorVersion == sys.version_info[1])

def isOlderThanPythonVersion(majorVersion, minorVersion):
    return (majorVersion > sys.version_info[0]) or (majorVersion  == sys.version_info[0] and minorVersion > sys.version_info[1])
        
def launchHTTPServer(port, handler):  
    log.info("HTTP Server startup on port '" + str(port) + "'.")
    server = FireworksHTTPServer(('', port), handler)
    server.serve_forever()
    return server
 

def findNthSubstring(stringToSearchInto, substringToFind, occurence):
    start = stringToSearchInto.find(substringToFind)
    while start >= 0 and occurence > 1:
        start = stringToSearchInto.find(substringToFind, start+len(substringToFind))
        occurence -= 1
    return start


def getRoundedTimeDifference(timeNow, timeThen, rounding):
    return str(round(timeNow - timeThen, rounding))

def getCurrentHostname():
    result = ""
    try:
        result = socket.gethostbyname( socket.gethostname() )
    except Exception:
        result = socket.gethostname()
    
    return result
        
def serializeListToFile(listToSerialize, file):
    result = None
    
    try:
        log.debug("Attempting to serialize list and write to file '" + file + "'")
        output = open(file, 'wb')
        cPickle.dump(listToSerialize, output)

        result = file

    except:
        log.critical("Unable to serialize list and write to file '" + file + "'")

    return result 

def deserializeListFromFile(file):
    result = None
    try:
        log.debug("Attempting to deserialize list from file '" + file + "'")
        input = open(file, 'rb')
        result = cPickle.load(input)


    except:
        log.critical("Unable to deserialize list from file '" + file + "'")

    return result

def createCustomLogger(logFilename, logFormat, logLevel):
    log.info("Attempting to create custom log file '" + logFilename + "'")
    fileHandler = logging.FileHandler(logFilename)
    fileHandler.setFormatter(logging.Formatter(logFormat))
    fileHandler.setLevel(logLevel)
    return fileHandler

def acquireLock(lockFilename, isDebug):
    from lib.FileLocker import flock
    log.debug("Attempting to acquire lock '" + lockFilename + "'")
    lock = flock(lockFilename, isDebug).acquire()
    if (not lock):
        raise Exception("Lock file '" + lockFilename + "' already exists. This fireworks instance is currently used by someone else.")
    return lock

def isFileEmpty(filename):
    result = False
    try:
        log.debug("Checking if module '" + filename + "' is empty")
        result = os.path.getsize(filename) == 0
    except OSError:
        pass
    
    return result

def isRequiredFileEmpty(filename):
    if isFileEmpty(filename):
        die("Required file '" + lib.OptParser.options.module + "' is empty.")
    else:
        pass

# Initialize script global properties
scriptGlobals = ScriptGlobals();

# Initialize loggers
logging.ColorFormatter = ColorFormatter
logging.config.fileConfig(scriptGlobals.logProperties)
log = logging.getLogger(scriptGlobals.defaultLogger)
