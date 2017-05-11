# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

from mwana.apps.labresults.models import Result
from mwana.apps.locations.models import Location


class InfantResultAlert(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending Action'),
        ('alerted', 'Staff Alerted'),
        ('identified', 'Client identified & seen by facility'),
        ('treatment_started', 'Client Started on treatment'),
        ('ltf', 'Lost to Followup'),
        ('deceased', 'Deceased'),
    )
    NOTIFICATION_CHOICES = (
        ('new', 'New'),
        ('notified', 'Staff Alerted'),
    )

    result = models.ForeignKey(Result)
    followup_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notification_status = models.CharField(max_length=20, choices=NOTIFICATION_CHOICES, default='new', editable=False)
    created_on = models.DateTimeField(default=datetime.now, editable=False, null=True, blank=True)

    # fields for faster reporting
    location = models.ForeignKey(Location, editable=False, null=True, blank=True)
    birthdate = models.DateField(editable=False, null=True, blank=True)
    sex = models.CharField(editable=False, max_length=1, blank=True)
    verified = models.NullBooleanField(editable=False, null=True, blank=True)
    collected_on = models.DateField(editable=False, blank=True, null=True)
    received_at_lab = models.DateField(editable=False, blank=True, null=True)
    processed_on = models.DateField(editable=False, blank=True, null=True)
    date_reached_moh = models.DateField(editable=False, blank=True, null=True)
    date_retrieved = models.DateField(editable=False, blank=True, null=True)
    treatment_start_date = models.DateField(blank=True, null=True)
    treatment_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Treatment #')
    lab = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        if self.result:
            self.location = self.result.clinic
            self.birthdate = self.result.birthdate
            self.sex = self.result.sex
            self.verified = self.result.verified
            self.collected_on = self.result.collected_on
            self.received_at_lab = self.result.entered_on
            self.processed_on = self.result.processed_on
            self.date_reached_moh = self.result.arrival_date
            self.date_retrieved = self.result.result_sent_date
            self.lab = self.result.payload.source

        if self.notification_status == 'notified':
            if self.followup_status == 'pending':
                self.followup_status = 'alerted'
        super(InfantResultAlert, self).save(*args, **kwargs)

    def __unicode__(self):
        return "Client ID=%s, Lab ID=%s" % (self.result.requisition_id, self.result.sample_id)


class InfantResultAlertViews(models.Model):
    alert = models.ForeignKey(InfantResultAlert, editable=False)
    seen_by = models.ForeignKey(User, editable=False)

    def __unicode__(self):
        return "%s viewed by %s" % (self.alert, self.seen_by)

    class Meta:
        verbose_name_plural = "Infant Result Alert Views"


class EmailRecipientForInfantResultAlert(models.Model):
    user = models.ForeignKey(User)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return "%s: Enabled? %s" % (self.user, self.is_active)