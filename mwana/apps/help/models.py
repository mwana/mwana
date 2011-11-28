# vim: ai ts=4 sts=4 et sw=4
from django.db import models
from rapidsms.models import Connection
import datetime

from django.contrib.auth.models import User

STATUS_CHOICES = (
    ("P", "pending"),
    ("A", "active"),
    ("R", "resolved"),
    ("C", "closed"),
)

class HelpRequest(models.Model):
    """A request for help"""
    
    requested_by = models.ForeignKey(Connection)
    requested_on = models.DateTimeField(default=datetime.datetime.utcnow)
    additional_text = models.CharField(max_length=160)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="P")
    comments = models.TextField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, null=True, blank=True)

    def __unicode__(self):
        contact = self.requested_by.contact.name if self.requested_by.contact \
                    else self.requested_by.identity
        problem = self.additional_text if self.additional_text else '<NO MORE INFO>'
        return "%s asks for help with '%s' on %s"  % (contact, problem, self.requested_on)
        
