def detailedInstallationReportTemplate(moduleName, action, serverAddress, pwd, guid, platform, username, build, revision, envprops, prevbuild=None, prevrevision=None):
    return '''
_________________________________________

 CRM Installation Execution Report
_________________________________________

Module name            : %s
Hudson Build           : %s (previous was %s)
Revision               : %s (previous was %s)
Action                 : %s
ActionBundle GUID      : %s
Server address         : %s
Execution directory    : %s
Platform               : %s
Username               : %s
Environment Properties : %s

 ''' % (moduleName, build, prevbuild, revision, prevrevision, action, guid, serverAddress, pwd, platform, username, envprops)