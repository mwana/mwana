# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.locations.models import Location
from django.db import models
from rapidsms.models import Contact
from django.contrib.auth.models import User


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


class Support(models.Model):
    user = models.ForeignKey(User)
    is_active = models.BooleanField(default=False)

    def __unicode__(self):
        return ("%s %s %s" % (self.user.username, self.user.first_name, self.user.last_name)).strip()


class LostContactsNotification(models.Model):
    sent_to = models.ForeignKey(Support)
    facility = models.ForeignKey(Location)
    date = models.DateField(auto_now_add=True)