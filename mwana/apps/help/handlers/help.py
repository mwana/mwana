#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.models import Contact
from mwana.apps.help.models import HelpRequest
from rapidsms.messages.outgoing import OutgoingMessage

RESPONSE           = "Sorry you're having trouble%(person)s. Your help request has been forwarded to a support team member and they will call you soon."
ANONYMOUS_FORWARD  = "Someone has requested help. Please call them at %(phone)s as soon as you can!"
CONTACT_FORWARD    = "%(name)s has requested help. Please call them at %(phone)s as soon as you can!"
CON_LOC_FORWARD    = "%(name)s at %(location)s has requested help. Please call them at %(phone)s as soon as you can!"
ADDITIONAL_INFO    = "Their message was: %(message)s"

class HelpHandler(KeywordHandler):
    """
    A simple help app, that optionally lets you forward requests to help admins
    """

    keyword = "help|helpme|support"
    
    
    
    def help(self):
        # Because we want to process this with just an empty keyword, rather
        # than respond with a help message, just call the handle method from
        # here.
        self.handle("")
    
    def handle(self, text):
        
        # create the "ticket" in the db
        HelpRequest.objects.create(requested_by=self.msg.connection,
                                   additional_text=text)
        
        params = {"phone": self.msg.connection.identity}
        resp_template = ANONYMOUS_FORWARD
        if self.msg.connection.contact:
            params["name"] = self.msg.connection.contact.name
            if self.msg.connection.contact.location:
                params["location"] = self.msg.connection.contact.location
                resp_template = CON_LOC_FORWARD
            else: 
                resp_template = CONTACT_FORWARD
        
        if text:
            resp_template = resp_template + " " + ADDITIONAL_INFO
            params["message"] = text

        for help_admin in Contact.objects.filter(is_help_admin=True):
            OutgoingMessage(help_admin.default_connection, resp_template, **params).send()
        
        person_arg = " " + self.msg.connection.contact.name if self.msg.connection.contact else ""
        self.respond(RESPONSE, person=person_arg)
                                         
        