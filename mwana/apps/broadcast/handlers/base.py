#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.messages.outgoing import OutgoingMessage

HELP_TEXT = "To send a message to %(group)s send keyword %(group)s followed by the contents of your message."
UNREGISTERED = "You must be registered with a clinic to use the broadcast feature. Please ask your clinic team how to register, or respond with keyword 'HELP'" 

class BroadcastHandler(KeywordHandler):
    """Broadcast handler"""
    
    def help(self):
        self.respond(HELP_TEXT, group=self.group_name)
    
    @property
    def group_name(self):
        raise NotImplementedError("subclasses must override this property!")
    
    def broadcast(self, text, contacts):
        message_body = "%(text)s [from %(user)s to %(group)s]"
        for contact in contacts:
            OutgoingMessage(contact.default_connection, message_body,
                            **{"text": text, 
                               "user": self.msg.contact.name, 
                               "group": self.group_name}).send()
        return True