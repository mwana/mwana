# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

from mwana.const import CLINIC_SLUGS
from mwana.apps.labresults.models import Result
from mwana.apps.labtests.models import Result as ViralLoadResult
from mwana.apps.locations.models import Location


class InfantResultAlert(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending Action'),
        ('alerted', 'Managers Alerted'),
        ('identified', 'Client identified'),
        ('seen', 'Client Seen by facility'),
        ('treatment_started', 'Client Started on treatment'),
        ('referred', 'Referred'),
        ('deceased', 'Deceased'),
        ('ltf', 'Lost to Follow-up'),
        ('defaulted', 'Defaulted'),
        ('unknown', 'Unknown'),
    )
    NOTIFICATION_CHOICES = (
        ('new', 'New'),
        ('notified', 'Staff Alerted'),
        ('closed', 'Closed'),
    )

    result = models.ForeignKey(Result)
    followup_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Action')
    notification_status = models.CharField(max_length=20, choices=NOTIFICATION_CHOICES, default='new', editable=False)
    created_on = models.DateTimeField(default=datetime.now, editable=False, null=True, blank=True,
                                      verbose_name='First Alert Date')

    # fields for faster reporting
    location = models.ForeignKey(Location, editable=False, null=True, blank=True,
                                 limit_choices_to={"type__slug__in": list(CLINIC_SLUGS),})
    referred_to = models.ForeignKey(Location, related_name='referred_to', null=True, blank=True,
                                    limit_choices_to={"type__slug__in": list(CLINIC_SLUGS),})
    birthdate = models.DateField(editable=False, null=True, blank=True, verbose_name='DOB')
    sex = models.CharField(editable=False, max_length=1, blank=True)
    verified = models.NullBooleanField(editable=False, null=True, blank=True)
    collected_on = models.DateField(editable=False, blank=True, null=True)
    received_at_lab = models.DateField(editable=False, blank=True, null=True)
    processed_on = models.DateField(editable=False, blank=True, null=True)
    date_reached_moh = models.DateField(editable=False, blank=True, null=True)
    date_retrieved = models.DateField(editable=False, blank=True, null=True)
    treatment_start_date = models.DateField(blank=True, null=True)
    notes = models.CharField(max_length=120, blank=True, null=True)
    lab = models.CharField(max_length=100, editable=False)

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
        if self.notification_status and self.followup_status not in ['pending', 'alerted']:
            self.notification_status = 'closed'
        super(InfantResultAlert, self).save(*args, **kwargs)

    def __unicode__(self):
        return "Client ID=%s, Lab ID=%s" % (self.result.requisition_id, self.result.sample_id)

    def parent(self):
        if self.id:
            return self.location.parent


class ViralLoadAlert(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending Action'),
        ('alerted', 'Managers Alerted'),
        ('identified', 'Client identified'),
        ('seen', 'Client Seen by facility'),
        ('iac_started', 'Intensive adherence counselling started'),
        ('regimen_changed', 'Changed drug regimen'),
        ('deceased', 'Deceased'),
        ('ltf', 'Lost to Follow-up'),
        ('defaulted', 'Defaulted'),
        ('unknown', 'Unknown'),
    )
    NOTIFICATION_CHOICES = (
        ('new', 'New'),
        ('notified', 'Staff Alerted'),
        ('closed', 'Closed'),
    )
    SEX_CHOICES = (
        ('m', 'Male'),
        ('f', 'Female'),
    )

    result = models.ForeignKey(ViralLoadResult)
    numeric_result = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=0, verbose_name='cp/mL')
    followup_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Action')
    notification_status = models.CharField(max_length=20, choices=NOTIFICATION_CHOICES, default='new', editable=False)
    created_on = models.DateTimeField(default=datetime.now, editable=False, null=True, blank=True,
                                      verbose_name='First Alert Date')

    # fields for faster reporting
    location = models.ForeignKey(Location, editable=False, null=True, blank=True,
                                 limit_choices_to={"type__slug__in": list(CLINIC_SLUGS),})
    referred_to = models.ForeignKey(Location, related_name='viral_loada_lert_referred_to', null=True, blank=True,
                                    limit_choices_to={"type__slug__in": list(CLINIC_SLUGS),})
    birthdate = models.DateField(editable=False, null=True, blank=True, verbose_name='DOB')
    age_in_years = models.PositiveIntegerField(null=True, blank=True, editable=False)
    sex = models.CharField(editable=False, max_length=1, blank=True, choices=SEX_CHOICES)
    verified = models.NullBooleanField(editable=False, null=True, blank=True)
    collected_on = models.DateField(editable=False, blank=True, null=True)
    received_at_lab = models.DateField(editable=False, blank=True, null=True)
    processed_on = models.DateField(editable=False, blank=True, null=True)
    date_reached_moh = models.DateField(editable=False, blank=True, null=True)
    date_retrieved = models.DateField(editable=False, blank=True, null=True)
    treatment_start_date = models.DateField(blank=True, null=True)
    notes = models.CharField(max_length=120, blank=True, null=True)
    lab = models.CharField(max_length=100, editable=False)

    def save(self, *args, **kwargs):
        if self.result:
            self.location = self.result.clinic
            self.birthdate = self.result.birthdate
            if self.result.age_unit.lower() in ('years', 'year', 'yrs', 'yr', 'y'):
                self.age_in_years = self.result.age
            self.sex = self.result.sex
            self.verified = self.result.verified
            self.collected_on = self.result.collected_on
            self.received_at_lab = self.result.entered_on
            self.processed_on = self.result.processed_on
            self.date_reached_moh = self.result.arrival_date
            self.date_retrieved = self.result.result_sent_date
            self.lab = self.result.payload.source
            try:
                self.numeric_result = Decimal(self.result.result)
            except ValueError:
                return False

        if self.notification_status == 'notified':
            if self.followup_status == 'pending':
                self.followup_status = 'alerted'
        if self.notification_status and self.followup_status not in ['pending', 'alerted']:
            self.notification_status = 'closed'
        super(ViralLoadAlert, self).save(*args, **kwargs)

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
    last_alert_number = models.PositiveIntegerField(editable=False, null=True, blank=True)
    last_alert_date = models.DateField(editable=False, null=True, blank=True)

    def __unicode__(self):
        return "%s: Enabled? %s" % (self.user, self.is_active)


class EmailRecipientForViralLoadAlert(models.Model):
    user = models.ForeignKey(User)
    is_active = models.BooleanField(default=True)
    last_alert_number = models.PositiveIntegerField(editable=False, null=True, blank=True)
    last_alert_date = models.DateField(editable=False, null=True, blank=True)

    def __unicode__(self):
        return "%s: Enabled? %s" % (self.user, self.is_active)

class ViralLoadAlertViews(models.Model):
    alert = models.ForeignKey(ViralLoadAlert, editable=False)
    seen_by = models.ForeignKey(User, editable=False)

    def __unicode__(self):
        return "%s viewed by %s" % (self.alert, self.seen_by)

    class Meta:
        verbose_name_plural = "Viral Load Alert Views"