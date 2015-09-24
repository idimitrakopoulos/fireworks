def detailedCleanInstallationReportTemplate(moduleName,version, action, serverAddress, pwd, guid, platform, username, build, revision, envprops, tmpdir):
    return '''
________________________________________

 MSM Action Execution Report
________________________________________

Module name            : %s
Module Version         : %s
Hudson Build           : %s
Revision               : %s
Action                 : %s
ActionBundle GUID      : %s
Server address         : %s
Execution directory    : %s
Platform               : %s
Username               : %s
Environment Properties : %s
tmp directory          : %s

 ''' % (moduleName,version, build, revision, action, guid, serverAddress, pwd, platform, username, envprops, tmpdir)
 
 
def detailedUpdateInstallationReportTemplate(moduleName,version, action, serverAddress, pwd, guid, platform, username, build, revision, envprops, prevVersion, prevBuild, prevRevision, tmpdir):
    return '''
_________________________________________

 MSM Action Execution Report
_________________________________________

Module name              : %s
Module installed Version : %s
Hudson installed Build   : %s
Module installed Revision: %s
Module previous Version  : %s
Hudson previous Build    : %s
Hudson previous Revision : %s
Action                   : %s
ActionBundle GUID        : %s
Server address           : %s
Execution directory      : %s
Platform                 : %s
Username                 : %s
Environment Properties   : %s
tmp directory            : %s

 ''' % (moduleName, version, build, revision, prevVersion, prevBuild, prevRevision, action, guid, serverAddress, pwd, platform, username, envprops, tmpdir)