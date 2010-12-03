# vim: ai ts=4 sts=4 et sw=4
from django.db import models
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Contact
from datetime import datetime

class BroadcastMessage(models.Model):
    
    contact = models.ForeignKey(Contact, related_name="broadcast_messages")
    group   = models.CharField(max_length=30)
    text    = models.TextField()
    date       = models.DateTimeField(default=datetime.utcnow)
    recipients = models.ManyToManyField(Contact, blank=True,
                                        related_name="broadcast_messages_received")
    
    # store a link to the message log tables as well, just in case we want
    # it later.  This is pretty redundant when both are running, but makes
    # our lives easier when that's not the case.
    logger_message = models.ForeignKey(Message, null=True, blank=True)
    
    def __unicode__(self):
        return "%s from %s to %s" % \
            (self.text, self.contact, self.group)
             
            
class BroadcastResponse(models.Model):
    
    broadcast = models.ForeignKey(BroadcastMessage)
    contact   = models.ForeignKey(Contact)
    text      = models.TextField()
    date      = models.DateTimeField(default=datetime.utcnow)
    
    logger_message = models.ForeignKey(Message)
    
    def __unicode__(self):
        return "%s from %s in response to %s" % \
            (self.text, self.contact, self.broadcast)
             
    