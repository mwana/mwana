# vim: ai ts=4 sts=4 et sw=4
from django.db import models
from mwana.apps.locations.models import Location
#from rapidsms.models import Connection
#from rapidsms.models import Contact

class Turnaround(models.Model):
    """
    A stub to display a view in django admin format for turnaround data
    """
    district = models.CharField(max_length=50)
    facility = models.CharField(max_length=100)
    transporting = models.IntegerField(blank=True, null=True)
    processing = models.IntegerField(blank=True, null=True)
    delays = models.IntegerField(blank=True, null=True)
    retrieving = models.IntegerField(blank=True, null=True)
    turnaround = models.IntegerField(blank=True, null=True)
    date_reached_moh = models.DateTimeField(blank=True, null=True)
    date_retrieved = models.DateField(blank=True, null=True)

class SupportedLocation(models.Model):
    location = models.ForeignKey(Location)
    supported = models.BooleanField(default=True)

class MessageGroup(models.Model):
    APP_LIST = (
                ('results160', 'Results160'),
                ('reminders', 'RemindMI')
                )
#    id = models.IntegerField()
    date = models.DateTimeField()
    text = models.TextField()
    direction = models.CharField(max_length=1)
    contact_type = models.CharField(max_length=50)
    keyword = models.CharField(max_length=15)
    changed_res = models.BooleanField()
    new_results = models.BooleanField()
    app = models.CharField(choices=APP_LIST, max_length=10)
    phone = models.CharField(max_length=12)
    backend = models.CharField(max_length=15)
    clinic = models.CharField(max_length=20)
    before_pilot = models.BooleanField()

