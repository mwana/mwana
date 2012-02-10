# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from rapidsms.models import Contact


class MonitorMessageRecipient(models.Model):
    contact = models.ForeignKey(Contact, limit_choices_to={'types__slug': 'worker',
    'is_help_admin':True, 'is_active':True})
    receive_sms = models.BooleanField\
                    (default=False,
                     help_text="Whether this person should receive monitor messages.")

    def __unicode__(self):
        extra = "can NOT receive monitor messages"
        if self.receive_sms:
            extra = "can receive monitor messages"
        return "%s %s" % (self.contact.name, extra)
