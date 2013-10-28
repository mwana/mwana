# vim: ai ts=4 sts=4 et sw=4
import logging
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.messages.outgoing import OutgoingMessage
from mwana.apps.broadcast.models import BroadcastMessage
from mwana.const import get_hub_worker_type

HELP_TEXT = "To send a message to %(group)s send keyword %(keyword)s followed by the contents of your message."
UNREGISTERED = "You must be registered with a clinic to use the broadcast feature. Please ask your clinic team how to register, or respond with keyword 'HELP'" 
logger = logging.getLogger(__name__)


class BroadcastHandler(KeywordHandler):
    """Broadcast handler"""
    
    def help(self):
        self.respond(HELP_TEXT, group=self.group_name,
                     keyword=self.keyword.split('|')[0].upper())
    
    @property
    def group_name(self):
        raise NotImplementedError("subclasses must override this property!")
    
    def broadcast(self, text, contacts):
        vars = dict(user = self.msg.contact.name, text = text, group = self.group_name)
        message_body = "%(text)s [from %(user)s to %(group)s]" % vars
        for contact in contacts.exclude(types=get_hub_worker_type()):
            if contact.default_connection is None:
                logger.info("Can't send to %s as they have no connections" % contact)
            else:
                OutgoingMessage([contact.default_connection], message_body).send()
        
        logger_msg = getattr(self.msg, "logger_msg", None) 
        if not logger_msg:
            logger.error("No logger message found for %s. Do you have the message log app running?" %\
                       self.msg)
        bmsg = BroadcastMessage.objects.create(logger_message=logger_msg,
                                               contact=self.msg.contact,
                                               text=text, 
                                               group=self.group_name)
        bmsg.recipients = contacts
        bmsg.save()
        return True
