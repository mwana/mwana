#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers import KeywordHandler
from mwana.apps.supply.models import SupplyType, SupplyRequest
from mwana.apps.registration.handlers.register import RegisterHandler

UNGREGISTERED = "Sorry, you must be registered with Results160 to report DBS samples sent. If you think this message is a mistake, respond with keyword 'HELP'"
SENT          = "Hello %(name)s! We received your notification that %(count)s DBS samples were sent to us today from %(clinic)s. We will notify you when the results are ready."
HELP          = "To report DBS samples sent, send SENT <NUMBER OF SAMPLES>"
SORRY         = "Sorry, we didn't understand that message."

class SentHandler(KeywordHandler):
    """
    """

    keyword = "sent"

    def help(self):
        self.respond(HELP)

    def handle(self, text):
        
        if not self.msg.contact:
            self.respond(UNGREGISTERED)
            return
        
        try:
            count = int(text.strip())
        except ValueError:
            self.respond("%s %s" % (SORRY, HELP))
            
        # TODO: maybe record this somewhere 
        self.respond(SENT, name=self.msg.contact.name, count=count,
                     clinic=self.msg.contact.location)
                     
        