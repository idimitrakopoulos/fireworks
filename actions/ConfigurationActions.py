from lib.Toolkit import log, scriptGlobals, replaceStringsInFileUsingAnotherFile, appendLineToFileAfterLine, appendLineToFileBeforeLine, removeLineFromFile, addCronJob, grepFile
from actions.Action import Action
import lib.OptParser

class ConfigureTemplateFile(Action):
    '''
    DO: Configure a template file with tags such as ${TAGNAME} using another file that has the values in the form of
    a Java property file
    UNDO: n/a
    '''
    def __init__(self, moduleName, valueFilename, templateFilename): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.moduleName = moduleName
        self.valueFilename = valueFilename
        self.templateFilename = templateFilename
        
        Action.__init__(self)                
        
    def __call__(self): 
        replaceStringsInFileUsingAnotherFile(self.moduleName, self.valueFilename, self.templateFilename)
        
    def undo(self):
        pass

    def report(self):
        log.info("Configured '" + self.templateFilename + "' using '" + self.valueFilename +"' from section '" + self.moduleName + "'.")
        

class AddLineToFile(Action):
    '''
    DO: Add a specific line to a file.
    UNDO: Remove the specific line from file
    '''
    def __init__(self, lineToFind, lineToAppend, fileName, tmpFilename, appendStyle): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.lineToFind = lineToFind
        self.lineToAppend = lineToAppend
        self.fileName = fileName
        self.tmpFilename = tmpFilename
        self.appendStyle = appendStyle
        
        Action.__init__(self)                
        
    def __call__(self): 
        if self.appendStyle == scriptGlobals.appendStyleEnum.BEFORE:
            appendLineToFileBeforeLine(self.lineToFind, self.lineToAppend, self.fileName, self.tmpFilename)
        else:
            appendLineToFileAfterLine(self.lineToFind, self.lineToAppend, self.fileName, self.tmpFilename)
        
    def undo(self):
        removeLineFromFile(self.lineToFind, self.fileName, self.tmpFilename)

    def report(self):
        log.info("Configured '" + self.templateFilename + "' using '" + self.valueFilename +"' from section '" + self.moduleName + "'.")

        
class AddCronJob(Action):
    '''
    DO: Add a cron job to crontab
    UNDO: n/a
    
    e.g. 
    
    AddCronJob("30     18     *     *     *         touch /home/idimitrakopoulos/tmp/kitsos")
    '''
    def __init__(self, cronJobLine): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.cronJobLine = cronJobLine
        
        Action.__init__(self)                
        
    def __call__(self): 
        addCronJob(self.cronJobLine)
        
    def undo(self):
        pass

    def report(self):
        log.info("Added cron job '" + self.cronJobLine + "' to crontab")        


class CheckFileConfigurationIsComplete(Action):
    '''
    DO: Checks a configuration file to see if any ${TAG} exist and provides a warning. Reported in the end of the operation as a warning
    UNDO: n/a
    '''
    def __init__(self, filename): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.filename = filename
        self.reportText = None
        
        Action.__init__(self)                
        
    def __call__(self): 
        if grepFile("\${", self.filename):
            self.reportText = "File '" + self.filename + "' contains values not contained in '" + lib.OptParser.options.envprops + "'" 
        
    def undo(self):
        pass

    def report(self):
        if (self.reportText): log.warn(self.reportText)     
        
        

class FinalReportingAction(Action):
    '''
    DO: Print a specific string at the final report
    UNDO: n/a
    '''
    def __init__(self, doReport, undoReport): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.doReport = doReport
        self.undoReport = undoReport
        self.reportTxt = ""
        
        Action.__init__(self)                
        
    def __call__(self): 
        self.reportTxt = self.doReport
        
    def undo(self):
        if (self.undoReport): self.reportTxt = self.undoReport

    def report(self):
        log.info(self.reportTxt)        