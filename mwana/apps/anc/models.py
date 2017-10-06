# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime, timedelta
from datetime import date

from django.contrib.auth.models import User
from django.db import models
from rapidsms.models import Connection

from mwana.const import CLINIC_SLUGS
from mwana.apps.locations.models import Location


class EducationalMessage(models.Model):
    gestational_age = models.PositiveIntegerField(null=True, blank=True)  # in weeks
    text = models.CharField(max_length=300)

    class Meta:
        unique_together = ('gestational_age', 'text')

    def __unicode__(self):
        return self.text


class CommunityWorker(models.Model):
    name = models.CharField(max_length=255)
    facility = models.ForeignKey(Location, related_name='anc_chw_location')
    zone = models.CharField(max_length=50, null=True, blank=True)
    connection = models.ForeignKey(Connection, related_name='anc_chw_connection', editable=False)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return "%s at %s" % (self.connection.identity, self.facility.name)

    class Meta:
        unique_together = ('connection', 'is_active')


class Client(models.Model):
    STATUS_CHOICES = (
        ('pregnant', 'Pregnant'),
        ('miscarriage', 'Miscarried'),
        ('stillbirth', 'Still-birth'),
        ('birth', 'Normal birth'),
        ('stop', 'Client opted out'),
        ('deprecated', 'Deprecated'),
        ('refused', 'Refused'),
    )
    facility = models.ForeignKey(Location, related_name='anc_client_location')
    connection = models.ForeignKey(Connection, related_name='anc_client_connection', editable=False)
    is_active = models.BooleanField(default=True)
    phone_confirmed = models.BooleanField(default=False)
    age_confirmed = models.BooleanField(default=False)
    community_worker = models.ForeignKey(CommunityWorker, blank=True, null=True)
    lmp = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pregnant')
    date_created = models.DateTimeField(default=datetime.now, editable=False)
    gestation_at_subscription = models.PositiveIntegerField()

    def __unicode__(self):
        return "%s at %s" % (self.connection.identity, self.facility.name)

    class Meta:
        unique_together = ('is_active', 'connection', 'lmp')
        verbose_name = 'Client Gestation'

    def is_eligible_for_messages(self):
        if not self.is_active:
            return False
        if self.status not in ['pregnant', 'birth']:
            return False
        return True

    def is_eligible_for_messages_by_pregnancy_status(self):
        return self.status in ['pregnant', 'birth']

    @classmethod
    def find_lmp(cls, gestational_age):
        return date.today() - timedelta(days=gestational_age * 7)

    def get_gestational_age(self):
        return (date.today() - self.lmp).days // 7


class SentClientMessage(models.Model):
    client = models.ForeignKey(Client)
    message = models.ForeignKey(EducationalMessage)
    date = models.DateTimeField(default=datetime.now, editable=False)

    def __unicode__(self):
        return "%s: %s" % (self.client, self.message.gestational_age)


class SentCHWMessage(models.Model):
    community_worker = models.ForeignKey(CommunityWorker)
    message = models.ForeignKey(EducationalMessage)
    date = models.DateTimeField(default=datetime.now, editable=False)

    def __unicode__(self):
        return "%s: %s" % (self.community_worker, self.message.gestational_age)


class WaitingForResponse(models.Model):
    client_gestation = models.ForeignKey(Client, editable=False)
    response = models.CharField(max_length=200, blank=True, null=True, editable=False)
    date_created = models.DateTimeField(default=datetime.now, editable=False)

    def __unicode__(self):
        return self.response


class FlowCommunityWorkerRegistration(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    facility = models.ForeignKey(Location, blank=True, null=True)
    zone = models.CharField(max_length=50, null=True, blank=True)
    connection = models.ForeignKey(Connection, editable=False)
    open = models.BooleanField(default=True)
    start_time = models.DateTimeField(editable=False)
    valid_until = models.DateTimeField(editable=False)

    def __unicode__(self):
        return ','.join(str(item) for item in [self.name, self.facility, self.zone, self.connection, self.open,
                                               self.start_time, self.valid_until])


class FlowClientRegistration(models.Model):
    community_worker = models.ForeignKey(CommunityWorker, blank=True, null=True)
    phone = models.CharField(max_length=13, null=True, blank=True)
    gestation_at_subscription = models.PositiveIntegerField(null=True, blank=True)
    open = models.BooleanField(default=True)
    start_time = models.DateTimeField(editable=False)
    valid_until = models.DateTimeField(editable=False)
