from django.db import models
from django.contrib.auth.models import User
from mwana.apps.locations.models import Location


class Server(models.Model):
    """A DHIS server instance."""
    name = models.CharField(max_length=160)
    url = models.URLField()
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.name


class Indicator(models.Model):
    """An instance of a indicator"""
    # optimise this later.
    LOCATION_CHOICES = [(x.slug, x.slug) for x in Location.objects.filter(
        send_live_results=True)]
    PERIOD_CHOICES = (
        ('y', 'Yearly'),
        ('q', 'Quarterly'),
        ('m', 'Monthly'),
        ('w', 'Weekly'),
    )
    server = models.ForeignKey(Server)
    name = models.CharField(max_length=160)
    location = models.CharField(choices=LOCATION_CHOICES, max_length=4,)
    period = models.CharField(choices=PERIOD_CHOICES, max_length=4,)
    rule = models.TextField()
    value = models.CharField(max_length=500, null=True, blank=True)
    dhis2_id = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.name


class Submission(models.Model):

    STATUS_CHOICES = (
        ('new', 'Unprocessed'),
        ('sent', 'Sent'),
    )

    date_sent = models.DateTimeField(null=True, blank=True)
    indicator = models.ForeignKey(Indicator)
    status = models.CharField(choices=STATUS_CHOICES, max_length=30)

    def __unicode__(self):
        return "%s submission for indicator %s" % (self.indicator.period,
                                                   self.indicator.name)
