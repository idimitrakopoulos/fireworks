from lib.Toolkit import log, moveDirOrFile, deleteDirOrFile, scriptGlobals, createDirectoriesRecursively,copyDirOrFile, generateRandomDirectoryUnderPath,\
    extractZipToDir, logExecute, extractFileFromZipToDir, changePathPermissions, getPathPermissions, logExecuteAndCaptureOutput, extractCompressedTarToDir, extractFileFromCompressedTarToDir, copyDirOrFile2, deleteListOfDirsOrFiles, logExecuteAndCheckErrorOutput,\
    changePathOwnership, removeDirectoriesRecursively, removeDirectory, createDirectory, isPythonVersion, isOlderThanPythonVersion
import os
from actions.Action import Action

class CopyDirOrFile(Action):
    '''
    DO: Copy a directory or a file to a specific location
    UNDO: Delete a directory or a file from a specific location
    
    '''
    def __init__(self, src, dst): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.src = src
        self.dst = dst
        
        Action.__init__(self)
        
    def __call__(self):
        copyDirOrFile(self.src, self.dst)
        
    def undo(self):
        deleteDirOrFile(self.dst)

    def report(self):
        log.info("cp -a " + self.src + " " + self.dst)
        
class CopyDirOrFile2(Action):
    '''
    DO: Copy the contents of a directory or a file to a specific location
    UNDO: Delete files or directories that were copied in the previous action. Non empty directories are left untouched.
    
    '''
    def __init__(self, src, dst): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.src = src
        self.dst = dst
        
        Action.__init__(self)
        
    def __call__(self):
        copyDirOrFile2(self.src, self.dst)
        
    def undo(self):      
        deleteListOfDirsOrFiles(self.dst, self.src)

    def report(self):
        log.info("cp -a " + self.src + " " + self.dst)            
     

class CopyDirOrFile3(Action):
    '''
    DO: Copy a directory or a file to a specific location
    UNDO: Copy back a directory or a file from a specific location
        
    '''
    def __init__(self, src, dst): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.src = src
        self.dst = dst
        
        Action.__init__(self)
        
    def __call__(self):
        copyDirOrFile(self.src, self.dst)
        
    def undo(self):
        copyDirOrFile(self.dst, self.src)

    def report(self):
        log.info("cp -a " + self.src + " " + self.dst)           


class MoveDirOrFile(Action):
    '''
    DO: Move a directory or a file
    UNDO: Move back a directory or a file    
    
    '''
    def __init__(self, src, dst): 
        log.debug(self.__class__.__name__ + " initialized")

        self.src = src
        self.dst = dst
        
        self.srcDirname = os.path.dirname(src)
        self.dstDirname = os.path.dirname(dst)

        self.srcBasename = os.path.basename(src)
        self.dstBasename = os.path.basename(dst)

        self.isSrcFile = os.path.isfile(src)
        self.isDstFile = os.path.isfile(dst)

        Action.__init__(self)        
                
    def __call__(self):
        moveDirOrFile(self.srcDirname + scriptGlobals.osDirSeparator + self.srcBasename,
                      self.dstDirname + scriptGlobals.osDirSeparator + self.dstBasename)

    def undo(self):
        # SD = source directory
        # DD = destination directory
        # sf = source file
        # df = destination file
        if (self.isSrcFile and not self.isDstFile and not os.path.isfile(self.dst)):
            # DO: moveDirOrFile("/SD/sf", "/DD") UNDO: moveDirOrFile("/DD/sf", "/SD")
            _from = self.dstDirname + scriptGlobals.osDirSeparator + self.dstBasename + scriptGlobals.osDirSeparator + self.srcBasename
            _to = self.srcDirname + scriptGlobals.osDirSeparator

        elif (self.isSrcFile and not self.isDstFile and os.path.isfile(self.dst)):
            # DO: moveDirOrFile("/SD/sf", "/DD/df") UNDO: moveDirOrFile("/DD/df", "/SD/sf")
            _from = self.dstDirname + scriptGlobals.osDirSeparator + self.dstBasename
            _to = self.srcDirname + scriptGlobals.osDirSeparator + self.srcBasename

        else:
            # Workaround fix since when moving a directory into another directory
            # shutil.move() behaves differently in python 2.4 or older
            if (isPythonVersion(2,4) or isOlderThanPythonVersion(2,4)):
                # DO: moveDirOrFile("/SD/SD", "/DD/DD") UNDO: moveDirOrFile("/DD/DD", "/SD/SD")
                _from = self.dstDirname + scriptGlobals.osDirSeparator + self.dstBasename
                _to = self.srcDirname + scriptGlobals.osDirSeparator + self.srcBasename
            else:
                # DO: moveDirOrFile("/SD/SD", "/DD/") UNDO: moveDirOrFile("/DD/SD", "/SD/")
                _from = self.dstDirname + scriptGlobals.osDirSeparator + self.srcBasename
                _to = self.srcDirname + scriptGlobals.osDirSeparator


        moveDirOrFile(_from, _to)

    def report(self):
        log.info("mv " + self.src + " " + self.dst)     

    
class CreateDirectory(Action):
    '''
    DO: Create a directory
    UNDO: Remove the directory

    e.g.

    CreateDirectory("/home/idimitrakopoulos/lala")
        
    '''
    def __init__(self, path): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.path = path
        
        Action.__init__(self)
        
    def __call__(self):
        createDirectory(self.path)
        
    def undo(self):
        removeDirectory(self.path)

    def report(self):
        log.info("mkdir " + self.path)


class CreateDirectoriesRecursively(Action):
    '''
    DO: Create directories recursively if needed
    UNDO: Remove the directories recursively (error will be raised if one of them isn't empty)

    e.g.

    CreateDirectoriesRecursively("/home/idimitrakopoulos/lala/lele/keke")
    '''
    def __init__(self, path):
        log.debug(self.__class__.__name__ + " initialized")

        self.path = path

        Action.__init__(self)

    def __call__(self):
        createDirectoriesRecursively(self.path)

    def undo(self):
        removeDirectoriesRecursively(self.path)

    def report(self):
        log.info("mkdir -p " + self.path)
                

class DeleteDirOrFile(Action):
    '''
    DO: Move a directory or a file to a random location under the workingDir
    UNDO: Move back a directory or a file from a random location under the workingDir
    
    '''
    def __init__(self, path): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.path = path
        self.tempLocation = generateRandomDirectoryUnderPath(scriptGlobals.workingDir)
        createDirectoriesRecursively(self.tempLocation)

        Action.__init__(self)    
        
    def __call__(self):
        moveDirOrFile(self.path, self.tempLocation + scriptGlobals.osDirSeparator)
        
    def undo(self):
        moveDirOrFile(self.tempLocation + scriptGlobals.osDirSeparator + self.path[self.path.rfind(scriptGlobals.osDirSeparator)+1:len(self.path)], self.path)
        
    def report(self):
        log.info("mv " + self.path + " " + self.tempLocation)         
        

class ExtractZipToDir(Action):
    '''
    DO: Extract a Zip file into a directory (will overwrite existing files/dirs)
    UNDO: n/a
    
    '''
    def __init__(self, zipFilename, location): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.zipFilename = zipFilename
        self.location = location
        
        Action.__init__(self)                
        
    def __call__(self): 
        extractZipToDir(self.zipFilename, self.location)
        
    def undo(self):
        pass

    def report(self):
        log.info("Extract '" + self.zipFilename + "' to '" + self.location +"'")                

class ExtractFileFromZipToDir(Action):
    '''
    DO: Extract a file from Zip file into a directory (will overwrite existing file)
    UNDO: n/a
    
    
    '''
    def __init__(self, zipFilename, filenameToExtract, location): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.zipFilename = zipFilename
        self.filenameToExtract = filenameToExtract
        self.location = location
        
        Action.__init__(self)                
        
    def __call__(self): 
        extractFileFromZipToDir(self.zipFilename, self.filenameToExtract, self.location)
        
    def undo(self):
        pass

    def report(self):
        log.info("Extract '" + self.filenameToExtract + "' from '" + self.zipFilename +"' to '" + self.location + "'")    


class ExtractCompressedTarToDir(Action):
    '''
    DO: Extract a Tar file into a directory (will overwrite existing files/dirs)
    UNDO: n/a
    
    e.g.
    
    ExtractCompressedTarToDir("/home/idimitrakopoulos/file.tar.gz", "r:gz", "/tmp")
    ExtractCompressedTarToDir("/home/idimitrakopoulos/file.tar.gz", "r:bz2", "/tmp")    
    
    '''
    def __init__(self, compressedFilename, compressionType, location): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.compressedFilename = compressedFilename
        self.compressionType = compressionType
        self.location = location
        
        Action.__init__(self)                
        
    def __call__(self): 
        extractCompressedTarToDir(self.compressedFilename, self.compressionType, self.location)
        
    def undo(self):
        pass

    def report(self):
        log.info("Extract '" + self.compressedFilename + "' to '" + self.location +"'")                


class ExtractFileFromCompressedTarToDir(Action):
    '''
    DO: Extract a file from Tar file into a directory (will overwrite existing file)
    UNDO: n/a
    
    e.g. 
    
    ExtractFileFromCompressedTarToDir("resources/lala.txt", "/home/idimitrakopoulos/file.tar.gz", "r:gz", "/tmp")
    ExtractFileFromCompressedTarToDir("resources/lala.txt", "/home/idimitrakopoulos/file.tar.gz", "r:bz2", "/tmp")
        
    '''
    def __init__(self, compressedFilename, compressionType, filenameToExtract, location): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.compressedFilename = compressedFilename
        self.compressionType = compressionType
        self.filenameToExtract = filenameToExtract
        self.location = location
        
        Action.__init__(self)                
        
    def __call__(self): 
        extractFileFromCompressedTarToDir(self.filenameToExtract, self.compressedFilename, self.compressionType, self.location)

    def undo(self):
        pass

    def report(self):
        log.info("Extract '" + self.filenameToExtract + "' from '" + self.compressedFilename +"' to '" + self.location + "'")
  
        
class ExecuteOSCommand(Action):
    '''
    DO: Execute the doCommand in the command line of the OS
    UNDO: Execute the undoCommand in the command line of the OS
    
    e.g.
    
    ExecuteOSCommand("mv /home/idimitrakopoulos/lalakis /home/idimitrakopoulos/tmp/lalakis", "mv /home/idimitrakopoulos/tmp/lalakis /home/idimitrakopoulos/lalakis")
    '''
    def __init__(self, doCommand, undoCommand):
        log.debug(self.__class__.__name__ + " initialized")
        
        self.doCommand = doCommand
        self.undoCommand = undoCommand

        
        Action.__init__(self)
        
    def __call__(self):
        logExecute(self.doCommand)
        
    def undo(self):
        if (self.undoCommand): logExecute(self.undoCommand)
        

    def report(self):
        log.info("Execute '" + self.doCommand + "'")                   


class ExecuteOSCommandAndCaptureOutput(Action):
    '''
    DO: Execute the doCommand in the command line of the OS and capture output and error streams
    UNDO: Execute the undoCommand in the command line of the OS and capture output and error streams
    
    e.g.
    
    ExecuteOSCommandAndCaptureOutput("mv /home/idimitrakopoulos/lalakis /home/idimitrakopoulos/tmp/lalakis", ["invalid", "exception", "connection refused"],"mv /home/idimitrakopoulos/tmp/lalakis /home/idimitrakopoulos/lalakis", ["invalid"])
    '''
    def __init__(self, doCommand, doTextListToFind, undoCommand, undoTextListToFind):
        log.debug(self.__class__.__name__ + " initialized")
        
        self.doCommand = doCommand
        self.doTextListToFind = doTextListToFind
        self.undoCommand = undoCommand
        self.undoTextListToFind = undoTextListToFind
        
        Action.__init__(self)

    # Method required for pickling.
    # It will delete any open streams
    def __getstate__(self):
        result = self.__dict__.copy()
        del result['doError']
        del result['doOutput']
        return result
        
    def __call__(self):
        self.doOutput, self.doError = logExecuteAndCheckErrorOutput(self.doCommand, self.doTextListToFind)

    def undo(self):
        if (self.undoCommand): 
            self.undoOutput, self.undoError = logExecuteAndCheckErrorOutput(self.undoCommand, self.undoTextListToFind)

    def report(self):
        log.info("Execute '" + self.doCommand + "'")          


class ChangePathPermissions(Action):
    '''
    DO: Chmod a file or directory recursively
    UNDO: Chmod back to original permissions of path folder (recursively)
          Note: The undo script will use the original path permissions to recursively revert all contained files
    
    e.g.
    
    ChangePathPermissions("/home/idimitrakopoulos/lalakis", stat.S_IEXEC|stat.S_IWRITE)
    
    or
    
    ChangePathPermissions("/home/idimitrakopoulos/lalakis", 0744) 
    
    Notice the 0 in front of 744 - If you're wondering why that leading zero is important, 
    it's because permissions are set as an octal integer, and Python automagically treats 
    any integer with a leading zero as octal. 
    '''
    def __init__(self, path, mode): 
        log.debug(self.__class__.__name__ + " initialized")

        self.path = path          
        self.doMode = mode
        self.undoMode = getPathPermissions(path)
     
        
        Action.__init__(self)
        
    def __call__(self):
        changePathPermissions(self.path, self.doMode)
        
    def undo(self):
        changePathPermissions(self.path, self.undoMode)

    def report(self):
        log.info("chmod -R " + str(self.doMode) + " " + self.path)
       
class ChangePathOwnership(Action):
    '''
    DO: Chown a file or directory recursively
    UNDO: Chown back to original ownership (the initial path's ownership will be propagated to all files/folders below)
    
    e.g. 
    
    ChangePathOwnership("/tmp", 1000, 1000)

    '''
    def __init__(self, path, uid, gid): 
        log.debug(self.__class__.__name__ + " initialized")

        self.path = path          
        self.uid = uid
        self.gid = gid
        self.undoStatObject = os.stat(path)
        
        Action.__init__(self)
        
    def __call__(self):
        changePathOwnership(self.path, self.uid, self.gid)
        
    def undo(self):
        changePathOwnership(self.path, self.undoStatObject.ST_UID, self.undoStatObject.ST_GID)
    
    def report(self):
        log.info("chown " + str(self.uid) + ":" + self.gid + " " + self.path)  
