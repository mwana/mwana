# vim: ai ts=4 sts=4 et sw=4
from mwana.const import get_lab_worker_type
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages.outgoing import OutgoingMessage
from mwana.apps.broadcast.models import BroadcastMessage
from mwana.const import get_hub_worker_type

HELP_TEXT = "To send a message to %(group)s send keyword %(keyword)s followed by the contents of your message."
UNREGISTERED = "You must be registered with a clinic to use the broadcast feature. Please ask your clinic team how to register, or respond with keyword 'HELP'" 

class BroadcastHandler(KeywordHandler):
    """Broadcast handler"""
    
    def help(self):
        self.respond(HELP_TEXT, group=self.group_name,
                     keyword=self.keyword.split('|')[0].upper())
    
    @property
    def group_name(self):
        raise NotImplementedError("subclasses must override this property!")
    
    def broadcast(self, text, contacts, sending_connection=None):
        message_body = "%(text)s [from %(user)s to %(group)s]"
        recipients = contacts.exclude(types__in=[get_hub_worker_type(), get_lab_worker_type()])
        for contact in recipients:
            if contact.default_connection is None:
                self.info("Can't send to %s as they have no connections" % contact)
            else:
                OutgoingMessage(contact.default_connection, message_body,
                                **{"text": text, 
                                   "user": self.msg.contact.name, 
                                   "group": self.group_name}).send()

        if recipients and sending_connection:
            OutgoingMessage(sending_connection, "Your message has been sent to %s people" % len(recipients)).send()

        logger_msg = getattr(self.msg, "logger_msg", None)
        if not logger_msg:
            self.error("No logger message found for %s. Do you have the message log app running?" %\
                       self.msg)
        bmsg = BroadcastMessage.objects.create(logger_message=logger_msg,
                                               contact=self.msg.contact,
                                               text=text, 
                                               group=self.group_name)
        bmsg.recipients = contacts
        bmsg.save()
        return True