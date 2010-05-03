#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact
import re

BYE_MSG   = "You have successfully unregistered, %(name)s. We're sorry to see you go."
ERROR_MSG = "Whoops - you tried to unregister from the system but I don't know who you are! Don't worry, you won't be receiving any messages from us."
    
class UnregisterHandler(KeywordHandler):
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
            name = self.msg.connection.contact.name
            # we just deactivate the contact, but don't delete it, because 
            # there could be all kinds of useful foreign key goodies attached.
            self.msg.connection.contact.is_active = False
            self.msg.connection.contact.save()
            # we also disassociate the contact from the connection
            self.msg.connection.contact = None
            self.msg.connection.save()
            self.respond(BYE_MSG, name=name)
        else:
            self.respond(ERROR_MSG)
            