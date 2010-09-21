from django.db import models
from rapidsms.contrib.locations.models import Location

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
    supported =models.BooleanField(default=True)
