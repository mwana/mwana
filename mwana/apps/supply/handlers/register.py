#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact
import re


class RegisterHandler(KeywordHandler):
    """
    """

    keyword = "register|reg|join"

    PATTERN = re.compile(r"^\s*(\S+)\s+(.+)$")
    
    def help(self):
        self.respond("To register, send JOIN <LOCATION CODE> <NAME>")

    def handle(self, text):
        m = self.PATTERN.search(text)
        if m is not None:
            location_code = m.groups()[0].strip()
            name = m.groups()[1].strip()
            try:
                location = Location.objects.get(slug__iexact=location_code)
                contact = Contact.objects.create(name=name, location=location)
                self.msg.connection.contact = contact
                self.msg.connection.save()
                self.respond("Thank you for registering, %(name)s! I've got you at %(location)s.",
                             name=contact.name, location=location.name)
            except Location.DoesNotExist:
                self.respond("Sorry, I don't know about a location with code %(code)s. Please check your code and try again.",
                             code=location_code)
        else:
            self.respond("Sorry, I didn't understand that. Make sure you send your location and name like: JOIN <LOCATION CODE> <NAME>") 
        
        
        

        