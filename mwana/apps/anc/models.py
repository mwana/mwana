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


class Client(models.Model):
    STATUS_CHOICES = (
        ('pregnant', 'Pregnant'),
        ('miscarriage', 'Miscarried'),
        ('stillbirth', 'Still-birth'),
        ('birth', 'Normal birth'),
        ('stop', 'Client opted out'),
        ('deprecated', 'Deprecated'),
    )
    facility = models.ForeignKey(Location, related_name='anc_client_location')
    connection = models.ForeignKey(Connection, related_name='anc_client_connection', editable=False)
    is_active = models.BooleanField(default=True)
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

    @classmethod
    def find_lmp(cls, gestational_age):
        return date.today() - timedelta(days=gestational_age * 7)

    def get_gestational_age(self):
        return (date.today() - self.lmp).days // 7


class SentMessage(models.Model):
    client = models.ForeignKey(Client)
    message = models.ForeignKey(EducationalMessage)
    date = models.DateTimeField(default=datetime.now, editable=False)

    def __unicode__(self):
        return "%s: %s" % (self.client, self.message.gestational_age)


class WaitingForResponse(models.Model):
    client_gestation = models.ForeignKey(Client, editable=False)
    response = models.CharField(max_length=200, blank=True, null=True, editable=False)
    date_created = models.DateTimeField(default=datetime.now, editable=False)

    def __unicode__(self):
        return self.response

