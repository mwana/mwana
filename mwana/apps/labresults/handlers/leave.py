#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact
import re

BYE_MSG   = "You have successfully left, %(name)s. We're sorry to see you go."
ERROR_MSG = "Whoops - you tried to leave the system but I don't know who you are! Don't worry, you won't be receiving any messages from us."
    
class RegisterHandler(KeywordHandler):
    """
    """

    keyword = "leave|unregister|unreg"
    
    def help(self):
        # Because we want to process this with just an empty keyword, rather
        # than respond with a help message, just call the handle method from
        # here.
        self.handle("")

    def handle(self, text):
        if self.msg.connection.contact:
            self.msg.connection.contact.delete()
            self.respond(BYE_MSG, name=self.msg.connection.contact.name)
        else:
            self.respond(ERROR_MSG)
            