# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from rapidsms.models import Contact
from mwana.apps.labresults.models import Payload, Result


class MonitorMessageRecipient(models.Model):
    contact = models.ForeignKey(Contact,
                                limit_choices_to={'types__slug': 'worker',
                                                  'is_help_admin': True,
                                                  'is_active': True})
    receive_sms = models.BooleanField(
        default=False,
        help_text="Whether this person should receive monitor messages.")

    def __unicode__(self):
        extra = "can NOT receive monitor messages"
        if self.receive_sms:
            extra = "can receive monitor messages"
        return "%s %s" % (self.contact.name, extra)


class MonitorSample(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('update', 'Updated'),
    )

    SYNC_CHOICES = (
        ('new', 'New sample from lab.'),
        ('update', 'Update data from lab.'),
        ('synced', 'Archived sample from lab.')
    )

    sample_id = models.CharField(max_length=20, help_text="ID from LIMS")
    payload = models.ForeignKey(Payload, null=True, blank=True,
                                help_text="Originating payload from lab.")
    result = models.ForeignKey(Result, null=True, blank=True,
                               help_text="Synchronised result from payload.")
    sync = models.CharField(choices=SYNC_CHOICES, max_length=15,
                            help_text="A new sample or an Update")
    status = models.CharField(choices=STATUS_CHOICES, max_length=15,
                              default='pending',
                              help_text="Synchronisation status.")
    raw = models.TextField(help_text="Raw value of the sample record.")
    hmis = models.CharField(max_length=10, null=True, blank=True,
                            help_text="HMIS Code for the facility.")
