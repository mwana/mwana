from django.db import models

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
    date = models.DateField(blank=True, null=True)
