import time
import threading
import urllib

class Timer(threading.Thread):
    def __init__(self, seconds, urlToHit):
        self.runTime = seconds
        self.urlToHit = urlToHit
        threading.Thread.__init__(self)
        self._stop = threading.Event()

    def stop (self):
        self._stop.set()
        
    def stopped (self):
        return self._stop.isSet()
        
    def run(self):
        from Toolkit import log
        for i in xrange(int(self.runTime)):
            time.sleep(1)
            log.debug("Time remaining: " + str(self.runTime-i) + " sec")
            if self.stopped(): 
                return
        
        log.debug("Time is up. Attempting to hit '" + self.urlToHit + "'")
        urllib.urlopen(self.urlToHit)

