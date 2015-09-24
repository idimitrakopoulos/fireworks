import threading
import sys, os
import time
import unicodedata


def fireworksAsciiHeader(version, revision, buildDate):
    return '''
                                 .''.
       .''.             *''*    :_\/_:     .
      :_\/_:   .    .:.*_\/_*   : /\ :  .'.:.'.
  .''.: /\ : _\(/_  ':'* /\ *  : '..'.  -=:o:=-
 :_\/_:'.:::. /)\*''*  .|.* '.\'/.'_\(/_'.':'.'
 : /\ : :::::  '*_\/_* | |  -= o =- /)\    '  *
  '..'  ':::'   * /\ * |'|  .'/.\'.  '._____
      *        __*..* |  |     :      |.   |' .---"|
       _*   .-'   '-. |  |     .--'|  ||   | _|    |
    .-'|  _.|  |    ||   '-__  |   |  |    ||      |
    |' | |.    |    ||       | |   |  |    ||      |
 ___|  '-'     '    ""       '-'   '-.'    '`      |____
___________________________________________________________
  _____.__                                   __            
_/ ____\__|______   ______  _  _____________|  | __  ______
\   __\|  \_  __ \_/ __ \ \/ \/ /  _ \_  __ \  |/ / /  ___/
 |  |  |  ||  | \/\  ___/\     (  <_> )  | \/    <  \___ \ 
 |__|  |__||__|    \___  >\/\_/ \____/|__|  |__|_ \/____  >
                       \/                        \/     \/ 
 
 Velti Fireworks Project (c) 2010-2011 Iason Dimitrakopoulos
 ___________________________________________________________\n

 Version: '%s r%s' @ %s

''' % (version, revision, buildDate)

def placeholderAscii():
    return '''\n
|fireworks|_____________________________________________________    
%s
________________________________________________________________
'''
    
def rollbackAsciiHeader():
    return placeholderAscii() % (''' __                
|__)_ |||_  _  _|  
| \(_)|||_)(_|(_|( ''')

def finalReportAsciiHeader():
    return placeholderAscii() % (''' __          __             
|_. _  _ |  |__)_ _  _  _|_ 
| || )(_||  | \(-|_)(_)| |_ 
                 |     ''')
    
def informationAsciiHeader():
    return placeholderAscii() % ('''     _                     
| _ (_ _  _ _  _ |_. _  _  
|| )| (_)| |||(_||_|(_)| )''')    

def dividerAscii():
    return "\n\n________________________________________________________________\n"



class SpinCursor(threading.Thread):
    ''' 
    Console spin cursor class 
    '''
    
    def __init__(self, msg='',maxspin=0,minspin=10,speed=5):
        # Count of a spin
        self.count = 0
        self.out = sys.stdout
        self.flag = False
        self.max = maxspin
        self.min = minspin
        # Any message to print first ?
        self.msg = msg
        # Complete printed string
        self.string = ''
        # Speed is given as number of spins a second
        # Use it to calculate spin wait time
        self.waittime = 1.0/float(speed*4)
        if os.name == 'posix':
            self.spinchars = (unicodedata.lookup('FIGURE DASH'),u'\\ ',u'| ',u'/ ')
        else:
            # The unicode dash character does not show
            # up properly in Windows console.
            self.spinchars = (u'-',u'\\ ',u'| ',u'/ ')        
        threading.Thread.__init__(self, None, None, "Spin Thread")
        
    def spin(self):
        """ Perform a single spin """

        for x in self.spinchars:
            self.string = self.msg + ">> " + x + "\r"
            self.out.write(self.string.encode('utf-8'))
            self.out.flush()
            time.sleep(self.waittime)

    def run(self):
        while (not self.flag):
            self.spin()
            self.count += 1

        # Clean up display...
        self.out.write(" "*(len(self.string) + 1))
        
    def stop(self):
        self.flag = True
        
if __name__ == "__main__":
    spin = SpinCursor(msg="Spinning...",minspin=5,speed=5)
    spin.start()

