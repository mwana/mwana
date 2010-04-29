#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.broadcast.handlers.base import BroadcastHandler, UNREGISTERED
from rapidsms.models import Contact
from mwana.util import get_clinic_or_default


class AllHandler(BroadcastHandler):
    
    group_name = "ALL"
    keyword = "ALL"
    
    def handle(self, text):
        if self.msg.contact is None or \
           self.msg.contact.location is None:
            self.respond(UNREGISTERED)
        
        location = get_clinic_or_default(self.msg.contact)
        
        contacts = Contact.active.location(location)\
                        .exclude(id=self.msg.contact.id)
        return self.broadcast(text, contacts)