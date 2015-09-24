headerTemplate = '''From: %s
To: %s
Subject: %s
'''
footerTemplate = '''

________________________________________________________________________________
Fireworks - Automatic Deployment Script - (c) 2010-2011 by Iason Dimitrakopoulos'''
bodyTemplate = '''%s'''
emailTemplate = '''%s
%s
%s'''

def constructHeader(sender, recipients, subject, headerTemplate):
    return headerTemplate % (sender, ", ".join(recipients), subject)

def constructFooter(footerTemplate):
    return footerTemplate

def constructBody(bodyText, bodyTemplate):
    return bodyTemplate % (bodyText)

def constructEmail(sender, recipients, subject, body):
    constructedHeader = constructHeader(sender, recipients, subject, headerTemplate)
    constructedBody = constructBody(body, bodyTemplate)
    constructedFooter = constructFooter(footerTemplate)
    constructedEmail = emailTemplate % (constructedHeader, constructedBody, constructedFooter)
     
    return constructedEmail

def restartPendingNotificationTemplate(moduleName, serverAddress, url, guid):
    return '''Hi, this is an automated notification!
    
The %s@%s server will be restarted, to prevent it from being restarted please hit:

%s

ActionBundle GUID: %s''' % (moduleName, serverAddress, url, guid)

def restartCancellationNotificationTemplate(moduleName, serverAddress, guid):
    return '''Hi, this is an automated notification!
    
The %s@%s server was cancelled. 

ActionBundle GUID: %s''' % (moduleName, serverAddress, guid)

def stopApplicationServerNotificationTemplate(moduleName, serverAddress, guid):
    return '''Hi, this is an automated notification!
    
The %s@%s server was stopped.

ActionBundle GUID: %s''' % (moduleName, serverAddress, guid)

def startApplicationServerNotificationTemplate(moduleName, serverAddress, guid):
    return '''Hi, this is an automated notification!
    
The %s@%s server was started.

ActionBundle GUID: %s''' % (moduleName, serverAddress, guid)

def killApplicationServerNotificationTemplate(moduleName, serverAddress, guid):
    return '''Hi, this is an automated notification!
    
The %s@%s server was killed.

ActionBundle GUID: %s''' % (moduleName, serverAddress, guid)

def detailedExecutionReportTemplate(version, revision, buildDate, moduleName, action, serverAddress, workingDir, pwd, guid, fireworksStateFile, platform, username):
    return '''____________________________

 Fireworks Execution Report
____________________________

This is to let you know that Fireworks was executed.

Fireworks Version      : %s r%s (build date: %s)
Module name            : %s
Action                 : %s
Execution GUID         : %s
Server address         : %s
Execution directory    : %s
Working directory      : %s
Fireworks State file   : %s
Platform               : %s
Username               : %s

 ''' % (version, revision, buildDate, moduleName, action, guid, serverAddress, pwd, workingDir,  fireworksStateFile, platform, username)