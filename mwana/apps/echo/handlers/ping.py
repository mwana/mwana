#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from rapidsms.contrib.handlers.handlers.base import BaseHandler
from rapidsms.errors import NoRouterError
import os

class PingHandler(BaseHandler):
    """
    Handle the (precise) message ``ping``, by responding with ``pong``.
    Useful for remotely checking that the router is alive.
    """

    
    @classmethod
    def dispatch(cls, router, msg):
        if msg.text == "ping":
            text = ''
            from rapidsms.router import router
            if not router.running:
#                raise NoRouterError()
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
            return msg.respond(text)
        

def ping_the_net():
    if os.system("ping -c 3 google.com"):
        #print "We're not connected!!!"
        return False
    else:
#        print "Things are fine!"
        return True