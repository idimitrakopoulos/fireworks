from lib.Toolkit import log, sendEmail
from actions.Action import Action
import lib.OptParser


class SendEmail(Action):
    '''
    DO: Send an email to specific recipients using SMTP
    UNDO: n/a
    
    e.g.
    
    SendEmail('from@domain.com', ['to@todomain.com', 'to2@todomain.com'], 'hello!', 'localhost', '25')
    '''
    
    def __init__(self, sender, receivers, subject, message, smtpServer, smtpPort): 
        log.debug(self.__class__.__name__ + " initialized")
        
        self.sender = sender
        self.receivers = receivers
        self.subject = subject
        self.message = message
        self.smtpServer = smtpServer
        self.smtpPort = smtpPort
        
        Action.__init__(self)
        
    def __call__(self):
        sendEmail(self.sender, self.receivers, self.subject, self.message, self.smtpServer, self.smtpPort)
        
    def undo(self):
        pass

    def report(self):
        if not lib.OptParser.options.silent:        
            log.info("Email sent from '" + self.sender + "' to '" + str(self.receivers) + "' through '" + self.smtpServer + ":" + self.smtpPort + "' with body '" + self.message + "'")
        else:
            log.info("Email sent was NOT sent from '" + self.sender + "' to '" + str(self.receivers) + "' through '" + self.smtpServer + ":" + self.smtpPort + "' with body '" + self.message + "'. The reason was that the user selected to perform a silent operation (i.e. no email notifications)")