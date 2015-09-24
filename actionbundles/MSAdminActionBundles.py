from actionbundles.ActionBundle import ActionBundle
from lib.Toolkit import generateGUID, log, getProcessPIDByPath, die, \
    createDirectoriesRecursively, scriptGlobals, sprintfOnDictionaryValues, \
    readPropertyFromPropertiesFile, grepFile, \
    runPostgresScript
from actions.FileSystemActions import ExtractZipToDir, CopyDirOrFile, \
    CopyDirOrFile2, ExtractFileFromZipToDir, ExecuteOSCommand, DeleteDirOrFile
import lib.OptParser
from actions.ConfigurationActions import ConfigureTemplateFile, \
    CheckFileConfigurationIsComplete
from actions.DatabaseActions import RunPostgresScriptFromFile, RunPostgresScript
import os


class MSAdminCleanInitAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)
  
        # Check if JBOSS is running
        if getProcessPIDByPath(module.targetDeploymentPath):die("The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")    
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()    
        log.info("Unique ActionBundle execution ID generated: " + guid)    
        
        # Prepare directory to unpack package
        module.subModule.unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")
        
        # Extract MS Admin package into tmp dir
        ExtractZipToDir(module.moduleFilename, module.subModule.unzippedPackagePath)    

        # Extract MANIFEST.MF
        ExtractFileFromZipToDir(module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeWarPath, module.relativeVersionInformationPath, module.subModule.unzippedPackagePath)    

        # Since MS is deployed on JBOSS some paths have an %s to allow a configurable 
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)

        # delete juddi-service.sar folder
        juddiServicePath = module.targetDeploymentPath + scriptGlobals.osDirSeparator + "server" + scriptGlobals.osDirSeparator + module.targetDeploymentProfile + scriptGlobals.osDirSeparator + "deploy" + scriptGlobals.osDirSeparator + "juddi-service.sar"
        if os.path.exists(juddiServicePath) :
            DeleteDirOrFile(juddiServicePath);
    # end    

class MSAdminUpdateInitAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)
        
        # Check if JBOSS is running
        if getProcessPIDByPath(module.targetDeploymentPath):die("The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")    
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()    
        log.info("Unique ActionBundle execution ID generated: " + guid)    

        # Prepare directory to unpack package
        module.subModule.unzippedPackagePath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "unzippedPackage")
        
        # Extract MS Admin package into tmp dir
        ExtractZipToDir(module.moduleFilename, module.subModule.unzippedPackagePath)    

        # Prepare directory to unpack package
        module.subModule.previousVersionBackupPath = createDirectoriesRecursively(scriptGlobals.workingDir + scriptGlobals.osDirSeparator + "previousVersionBackup")        

        # Extract new MANIFEST.MF
        ExtractFileFromZipToDir(module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeWarPath, module.relativeVersionInformationPath, module.subModule.unzippedPackagePath)    

        # Prepare directory to keep backups
        # Since MS is deployed on JBOSS some paths have an %s to allow a configurable 
        # profile, so do a little sprintf to fix them
        sprintfOnDictionaryValues(module.relativeConfigurationFiles, module.targetDeploymentProfile)
        sprintfOnDictionaryValues(module.relativeCopyableFilesOrFolders, module.targetDeploymentProfile)
        
        # end

class MSAdminCleanDBAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)
  
        # Check if JBOSS is running
        if getProcessPIDByPath(module.targetDeploymentPath):die("The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")    
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()    
        log.info("Unique ActionBundle execution ID generated: " + guid)    

        unzippedPackagePath = module.subModule.unzippedPackagePath

        # Import Clean DB script to Postgres DB
        dbUsername = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_DB_OWNER", module.name, lib.OptParser.options.envprops)
        dbPassword = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_DB_PASSWORD", module.name, lib.OptParser.options.envprops)
        dbHostName = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_HOSTNAME", module.name, lib.OptParser.options.envprops)
        dbName = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_DB_NAME", module.name, lib.OptParser.options.envprops)
        dbPort = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_PORT", module.name, lib.OptParser.options.envprops)
        tmpC = "jdbc:postgresql://" + dbHostName + ":" + dbPort + "/" + dbName
        
        # Run DB init script(s)
        for dbInitScript in module.relativeDatabaseInitFiles:
            # Replace Owner on init scripts             
            exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + dbInitScript
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)
            RunPostgresScriptFromFile(unzippedPackagePath + scriptGlobals.osDirSeparator + dbInitScript, dbUsername, dbPassword, tmpC)
            
        # Replace Owner on postgresLogTemplate            
        ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, scriptGlobals.postgresLogTemplateFile)
        # Add LOG table
        RunPostgresScriptFromFile(scriptGlobals.postgresLogTemplateFile, dbUsername, dbPassword, tmpC)
        
        # Find version/revision info
        versionInfo = grepFile(module.versionInformationRegex, unzippedPackagePath + scriptGlobals.osDirSeparator + "MANIFEST.MF")
        revisionInfo = grepFile(module.revisionInformationRegex, unzippedPackagePath + scriptGlobals.osDirSeparator + "MANIFEST.MF")
        
        versionInfo = (versionInfo.replace(module.versionInformationRegex, "")).strip()
        revisionInfo = (revisionInfo.replace(module.revisionInformationRegex, "")).strip()

        # Add one row per script executed in LOG table        
        for dbInitScript in module.relativeDatabaseInitFiles:
            lastExecutedPath, lastExecutedFilename = os.path.split(dbInitScript) 
            RunPostgresScript("INSERT INTO FIREWORKS_SCRIPT_LOG (INSTALLATION_ID, ACTION, MODULE_NAME, MODULE_VERSION, MODULE_REVISION, EXECUTED_SCRIPT, EXECUTED_ON) VALUES ('" + guid + "', '" + lib.OptParser.options.action + "', '" + module.name + "', '" + versionInfo + "', '" + revisionInfo + "', '" + lastExecutedFilename + "', CURRENT_TIMESTAMP);", dbUsername, dbPassword, tmpC)        

        # Already existing upgrade scripts must be logged because in the upcoming upgrade we need to run from there on
        log.info("Existing SQL patches will be logged in the log table so that the script will not run them again if you decise to update this version to latest")
        ls = os.listdir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath)
        ls.sort()
        for patch in ls:               
            RunPostgresScript("INSERT INTO FIREWORKS_SCRIPT_LOG (INSTALLATION_ID, ACTION, MODULE_NAME, MODULE_VERSION, MODULE_REVISION, EXECUTED_SCRIPT, EXECUTED_ON) VALUES ('" + guid + "', '" + lib.OptParser.options.action + "', '" + module.name + "', '" + versionInfo + "', '" + revisionInfo + "', '" + patch + "', CURRENT_TIMESTAMP);", dbUsername, dbPassword, tmpC)                
        #end
        
class MSAdminUpdateDBAB(ActionBundle):
    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)
  
        # Check if JBOSS is running
        if getProcessPIDByPath(module.targetDeploymentPath):die("The JBOSS server at '" + module.targetDeploymentPath + "' is up. Installation will not continue")    
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()    
        log.info("Unique ActionBundle execution ID generated: " + guid)    

        unzippedPackagePath = module.subModule.unzippedPackagePath

        # Import Clean DB script to Postgres DB
        dbUsername = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_DB_OWNER", module.name, lib.OptParser.options.envprops)
        dbPassword = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_DB_PASSWORD", module.name, lib.OptParser.options.envprops)
        dbHostName = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_HOSTNAME", module.name, lib.OptParser.options.envprops)
        dbName = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_DB_NAME", module.name, lib.OptParser.options.envprops)
        dbPort = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_PORT", module.name, lib.OptParser.options.envprops)
        tmpC = "jdbc:postgresql://" + dbHostName + ":" + dbPort + "/" + dbName
        
        
        
        # Find version/revision info
        versionInfo = grepFile(module.versionInformationRegex, unzippedPackagePath + scriptGlobals.osDirSeparator + "MANIFEST.MF")
        revisionInfo = grepFile(module.revisionInformationRegex, unzippedPackagePath + scriptGlobals.osDirSeparator + "MANIFEST.MF")
        
        versionInfo = (versionInfo.replace(module.versionInformationRegex, "")).strip()
        revisionInfo = (revisionInfo.replace(module.revisionInformationRegex, "")).strip()

        # Determine last executed script in DB
        dbUsername = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_DB_OWNER", module.name, lib.OptParser.options.envprops)
        dbPassword = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_DB_PASSWORD", module.name, lib.OptParser.options.envprops)
        dbHostName = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_HOSTNAME", module.name, lib.OptParser.options.envprops)
        dbName = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_DB_NAME", module.name, lib.OptParser.options.envprops)
        dbPort = readPropertyFromPropertiesFile("TARGET_POSTGRES_SRV_PORT", module.name, lib.OptParser.options.envprops)
        tmpC = "jdbc:postgresql://" + dbHostName + ":" + dbPort + "/" + dbName
        result = runPostgresScript("SELECT EXECUTED_SCRIPT FROM FIREWORKS_SCRIPT_LOG WHERE EXECUTED_ON IN (SELECT MAX(EXECUTED_ON) FROM FIREWORKS_SCRIPT_LOG);", dbUsername, dbPassword, tmpC)
        lastExecutedPath, lastExecutedFilename = os.path.split(result.strip());
        log.info("According to log table, the last script executed on '" + tmpC + "' was '" + lastExecutedFilename + "'")
        
        # Run scripts on DB
        ls = os.listdir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath)
        ls.sort()
        found = False
        for patch in ls:
            if found: 
                #Replace Owner
                exactExtractedLocation = unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + scriptGlobals.osDirSeparator + patch
                ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
                CheckFileConfigurationIsComplete(exactExtractedLocation)
                #Run Script
                RunPostgresScriptFromFile(unzippedPackagePath + scriptGlobals.osDirSeparator + module.relativeDatabaseUpgradeFilePath + scriptGlobals.osDirSeparator + patch, dbUsername, dbPassword, tmpC)
                # Log executed scripts                
                RunPostgresScript("INSERT INTO FIREWORKS_SCRIPT_LOG (INSTALLATION_ID, ACTION, MODULE_NAME, MODULE_VERSION, MODULE_REVISION, EXECUTED_SCRIPT, EXECUTED_ON) VALUES ('" + guid + "', '" + lib.OptParser.options.action + "', '" + module.name + "', '" + versionInfo + "', '" + revisionInfo + "', '" + patch + "', CURRENT_TIMESTAMP);", dbUsername, dbPassword, tmpC)                
            if  lastExecutedFilename.find(patch) > -1: found = True
        # end       
        

class MSAdminDeployWarAB(ActionBundle):
    '''
    classdocs
    '''


    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()    
        log.info("Unique ActionBundle execution ID generated: " + guid)
        
        # Copy marketing-suite-admin.war to deploy
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactExtractedLocation = module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)        
        # end 
        
class MSAdminDeployConfAB(ActionBundle):
    '''
    classdocs
    '''


    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()    
        log.info("Unique ActionBundle execution ID generated: " + guid)                
 
        # Configure marketing-suite-admin.properties using envprops
        # Configure mgage.properties using envprops
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + k
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, exactExtractedLocation)
            CheckFileConfigurationIsComplete(exactExtractedLocation)

        # Copy marketing-suite-admin.properties to conf
        # Copy mgage.properties to conf
        # Copy jboss-log4j.xml to conf
        for k, v in module.relativeConfigurationFiles.items():
            exactExtractedLocation = module.subModule.unzippedPackagePath + scriptGlobals.osDirSeparator + k
            exactTargetLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            CopyDirOrFile(exactExtractedLocation, exactTargetLocation)    
        # end        
        
class MSAdminBackUpAB(ActionBundle):
    '''
    classdocs
    '''


    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)
        
        # Generate a unique ActionBundle execution id
        guid = generateGUID()    
        log.info("Unique ActionBundle execution ID generated: " + guid)        
        
        previousVersionBackupPath = module.subModule.previousVersionBackupPath 
        unzippedPackagePath = module.subModule.unzippedPackagePath

        # Backup marketing-admin-webapp.war from deploy/
        # Backup esb.jar from deploy/
        # Backup ROOT.WAR/crossdmain.xml from deploy/ROOT.WAR
        log.info("######################## COPY ALL COPYABLE FILES ########################")        
        for k, v in module.relativeCopyableFilesOrFolders.items():
            exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            exactBackupLocation = module.subModule.previousVersionBackupPath + scriptGlobals.osDirSeparator + k
            CopyDirOrFile2(exactLocation, exactBackupLocation)        

             
        # Backup marketing-suite-deployment.properties from conf
        # Backup mgage.properties from conf
        # Backup jboss-log4j.xml from conf
        # Backup web.xml from marketing-admin-webapp.war/WEB-INF        
        log.info("######################## COPY ALL COPYABLE FILES ########################")        
        for k, v in module.relativeConfigurationFiles.items():
            exactLocation = module.targetDeploymentPath + scriptGlobals.osDirSeparator + v 
            exactBackupLocation = previousVersionBackupPath + scriptGlobals.osDirSeparator + k
            CopyDirOrFile2(exactLocation, exactBackupLocation)        

      
        log.info("######################## END OF COPY ########################")        
        # Extract old MANIFEST.MF
        ExtractFileFromZipToDir(previousVersionBackupPath + scriptGlobals.osDirSeparator + module.subModule.relativeWarPath, module.relativeVersionInformationPath, previousVersionBackupPath)    

        # Compare current and new versions
        log.info("Version currently installed    : " + grepFile(module.versionInformationRegex, previousVersionBackupPath + scriptGlobals.osDirSeparator + "MANIFEST.MF"))
        log.info("Revision currently installed   : " + grepFile(module.revisionInformationRegex, previousVersionBackupPath + scriptGlobals.osDirSeparator + "MANIFEST.MF"))
        log.info("Version to be installed        : " + grepFile(module.versionInformationRegex, unzippedPackagePath + scriptGlobals.osDirSeparator + "MANIFEST.MF"))        
        log.info("Revision to be installed       : " + grepFile(module.revisionInformationRegex, unzippedPackagePath + scriptGlobals.osDirSeparator + "MANIFEST.MF"))        
        #end    
            
class MSAdminRunJarAB(ActionBundle):
    '''
    classdocs
    '''


    def __init__(self, module):
        '''
        Constructor
        '''
        
        ActionBundle.__init__(self, module)

        unzippedPackagePath = module.subModule.unzippedPackagePath
        propertiesFileName = "upgrade-configuration.properties"
        
        # Run migration jars
        ls = os.listdir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeJarFilesPath)
        ls.sort()

        for zipFile in ls:
            # Extract MS Admin package into tmp dir
            ExtractZipToDir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeJarFilesPath + scriptGlobals.osDirSeparator + zipFile, unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeJarFilesPath)
               
            #Get jar name from zip name 
            jarFile = zipFile[:-4] + ".jar"
            
            # extract properties to current dir
            ExtractFileFromZipToDir(unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeJarFilesPath + scriptGlobals.osDirSeparator + jarFile, propertiesFileName, ".")
            
            # configure properties
            ConfigureTemplateFile(module.name, lib.OptParser.options.envprops, propertiesFileName)
            CheckFileConfigurationIsComplete(propertiesFileName)
                
            # add configured properties to zip    
            ExecuteOSCommand("zip -r " + unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeJarFilesPath + scriptGlobals.osDirSeparator + jarFile + " " + propertiesFileName, '')
            
            # delete properties from current dir
            DeleteDirOrFile(propertiesFileName);
            
            # run migration jar
            jarCommand = "java -jar " + unzippedPackagePath + scriptGlobals.osDirSeparator + module.subModule.relativeJarFilesPath + scriptGlobals.osDirSeparator + jarFile 
            log.info("Jar file " + jarFile + "will be executed with the following command \n" + jarCommand)    
            ExecuteOSCommand(jarCommand, '')

        #end    
