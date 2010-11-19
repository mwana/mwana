#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
import os

class PingHandler(KeywordHandler):
    """
    Handle the (precise) message ``ping``, by responding with ``pong``.
    Useful for remotely checking that the router is alive.
    """
    keyword = "ping|PING|Ping|P1ng|pong|PONG"
    
    def handle(self,text):
        pass
    
    def help(self):
        text = ''
        from rapidsms.router import router
        if not router.running:
            text += 'Router:DOWN'
        else:
            text += 'Router:UP'
            
        if ping_the_net():
            text += '|Internet:UP'
        else:
            text += '|Internet:DOWN'
             
        text += '|Backends:['
        b = router.backends
        for i in b:
            text += str(i) +':'+str(b[i].status())+', '
        text +=']'
        self.respond(text)
        return True
        

def ping_the_net():
    if os.system("ping -c 3 google.com"):
        #print "We're not connected!!!"
        return False
    else:
#        print "Things are fine!"
        return True