# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.locations.models import Location
from django.db import models
from datetime import datetime
from datetime import date
from rapidsms.models import Contact
from mwana.util import get_clinic_or_default


INCIDENT_TYPES = (
    ('dis', 'Disease'),
)


class Incident(models.Model):
    """
    An event such as a disease
    """
    name = models.CharField(max_length=50, null=False, blank=False, unique=True)
    indicator_id = models.CharField(max_length=8, null=True, blank=True, unique=True)
    abbr = models.CharField(max_length=8, null=True, blank=True)
    type = models.CharField(max_length=3, choices=INCIDENT_TYPES, default='dis')

    def __unicode__(self):
        if self.indicator_id:
            return "%s: %s" % (self.indicator_id, self.name)
        return self.name


class Alias(models.Model):
    """
    Helper class, more or less like a dictionary for alias of Incidents
    """
    incident = models.ForeignKey(Incident,blank=False, null=False)
    name = models.CharField(max_length=50, null=False,blank=False, unique=True)

    def __unicode__(self):
        return "%s - %s" % (self.name, self.incident)

    class Meta:
        verbose_name_plural = "Aliases"


class Report(models.Model):
    incident = models.ForeignKey(Incident, null=False, blank=False)
    value  = models.PositiveSmallIntegerField(null=False, blank=False)
    date = models.DateField(default=date.today, blank=False, null=False)
    logged_on = models.DateTimeField(default=datetime.now, blank=False, null=False)
    reporter = models.ForeignKey(Contact, blank=True, null=True)
    #Somehow redundant fields but useful for easy and faster reporting
    year = models.PositiveSmallIntegerField(null=False, blank=False)
    month = models.PositiveSmallIntegerField(null=False, blank=False)
    year = models.PositiveSmallIntegerField(null=False, blank=False)
    location = models.ForeignKey(Location)

    def __unicode__(self):
        return "%s - %s" % (self.incident, self.date)

    def save(self, *args, **kwargs):
        self.year = self.date.year
        self.month = self.date.year
        self.year = self.date.year
        self.location = get_clinic_or_default(self.reporter)
        super(Report, self).save(*args, **kwargs)


class Separator(models.Model):
    """
    Used to delimit/tokenize disease reports from a message sent. If this model
    is blank a default value will be used in the handlers
    """
    name = models.CharField(max_length=2, unique=True)

    def __unicode__(self):
        return self.name