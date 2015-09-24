from lib.Toolkit import log, runOracleScriptFromFile, runOracleScript, runPostgresScriptFromFile, runPostgresScript
from actions.Action import Action


class RunOracleScriptFromFile(Action):
    '''
    DO: Run an Oracle script from a file
    UNDO: n/a
    '''
    def __init__(self, scriptFilename, connectionString): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.scriptFilename = scriptFilename
        self.connectionString = connectionString
        
        Action.__init__(self)
        
    def __call__(self):
        runOracleScriptFromFile(self.scriptFilename, self.connectionString)
        
    def undo(self):
        pass
    
    def report(self):
        log.info("Executed '" + self.scriptFilename + "' on '" + self.connectionString +"'")


class RunOracleScript(Action):
    '''
    Do: Run an Oracle script from the command line
    UNDO: n/a
    '''
    def __init__(self, scriptText, connectionString, doCommit, headersOff): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.scriptText = scriptText
        self.connectionString = connectionString
        self.doCommit = doCommit
        self.headersOff = headersOff
        
        Action.__init__(self)
        
    def __call__(self):
        runOracleScript(self.scriptText, self.connectionString, self.doCommit, self.headersOff)
        
    def undo(self):
        pass
           
    def report(self):
        log.info("Executed '" + self.scriptText + "' on '" + self.connectionString +"'")

        
class RunPostgresScriptFromFile(Action):
    '''
    DO: Run an Postgres script from a file
    UNDO: n/a

    e.g.
     
    RunPostgresScriptFromFile("/home/idimitrakopoulos/lalakis", "mms", "mms", "jdbc:postgresql://10.1.2.88:5432/json")    
    '''
    def __init__(self, scriptFilename, username, password, connectionString): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.scriptFilename = scriptFilename
        self.username = username
        self.password = password
        self.connectionString = connectionString
        
        Action.__init__(self)
        
    def __call__(self):
        runPostgresScriptFromFile(self.scriptFilename, self.username, self.password, self.connectionString)
        
    def undo(self):
        pass

    def report(self):
        log.info("Executed '" + self.scriptFilename + "' on '" + self.username + "/" + self.password + "' '" + self.connectionString +"'")


class RunPostgresScript(Action):
    '''
    DO: Run an Postgres script
    UNDO: n/a
    
    e.g. 
    
    RunPostgresScript("select * from student", "mms", "mms", "jdbc:postgresql://10.1.2.88:5432/json")
    '''
    def __init__(self, script, username, password, connectionString): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.script = script
        self.username = username
        self.password = password
        self.connectionString = connectionString
        
        Action.__init__(self)
        
    def __call__(self):
        runPostgresScript(self.script, self.username, self.password, self.connectionString)
        
    def undo(self):
        pass
        
    def report(self):
        log.info("Executed '" + self.script + "' on '" + self.username + "/" + self.password + "' '" + self.connectionString +"'")            