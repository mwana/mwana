# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime
from django.db import models
from mwana.apps.locations.models import Location
from rapidsms.models import Contact


class HubSampleNotification(models.Model):
    """
    Records notifications that samples were sent.  This class
    is not linked to the Result class because we don't have
    individual sample ids, so we just include them in bulk.
    """

    contact  = models.ForeignKey(Contact, blank=True, null=True, related_name='sender')
    lab = models.ForeignKey(Location)
    count    = models.PositiveIntegerField()
    count_in_text = models.CharField(max_length=160, null=True, blank=True)
    date     = models.DateTimeField(default=datetime.now)
    clinic = models.ForeignKey(Location, blank=True, null=True, related_name='clinic')


    def __unicode__(self):
        return "%s DBS Samples from %s on %s" % \
            (self.count, self.lab.name, self.date.date())

class HubReportNotification(models.Model):
    """
    Records notifications/reports sent to hub to summarise DBS activities
    """
    REPORT_TYPES = (
    ('M','Monthly Report'),
    )

    contact  = models.ForeignKey(Contact, blank=True, null=True, related_name='receiver')
    lab = models.ForeignKey(Location)
    type    = models.CharField(choices=REPORT_TYPES, max_length=1, blank=True)
    samples = models.PositiveIntegerField()
    results = models.PositiveIntegerField()
    date     = models.DateField()
    date_sent     = models.DateTimeField(default=datetime.now)
   

    def __unicode__(self):
        return "%s DBS Summary for %s on %s" % \
            (self.lab.name, self.date, self.date_sent.date())