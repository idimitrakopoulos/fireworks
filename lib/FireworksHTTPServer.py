import string,cgi,time
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer



class FireworksHTTPServer (HTTPServer):
    """http server that reacts to self.stop flag"""
            
    def serve_forever (self):
        """Handle one request at a time until stopped."""
        self.stop = False
        
        # Continue serving requests until the kill request has been received
        while (not self.stop):
            self.handle_request()


class FireworksHTTPRequestHandler(BaseHTTPRequestHandler):  

    def do_GET(self):
        from Toolkit import log
        self.result = None
        try:
            log.info(self.path)
            
            if self.path == "/stopDelayedRestart.foo":
                self.send_response(200)
                self.send_header('Content-type',    'text/html')
                self.end_headers()
                self.wfile.write("OK Mr '" + str(self.client_address[0]) + "' the operation will be aborted...")
                # Stop the server
                log.debug("Client '" + str(self.client_address[0]) + "' cancelled the operation")
                self.server.stop = True
                self.server.result = 1 # someone cancelled
                
            if self.path == "/timeOut.foo":
                self.send_response(200)
                self.end_headers()               
                # Stop the server
                self.server.stop = True
                self.server.result = 0 # timeout occured
                                
            return
                
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)



