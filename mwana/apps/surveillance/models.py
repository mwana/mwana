# vim: ai ts=4 sts=4 et sw=4
from rapidsms.contrib.messagelog.models import Message
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
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)
    indicator_id = models.CharField(max_length=8, null=True, blank=True, unique=True)
    abbr = models.CharField(max_length=8, null=True, blank=True)
    type = models.CharField(max_length=3, choices=INCIDENT_TYPES, default='dis')
    
    def __unicode__(self):
        if self.indicator_id:
            return "%s: %s" % (self.indicator_id, self.name)
        return self.name

    def save(self, *args, **kwargs):
        if self.name == self.name.lower():
            self.name = self.name.title()
        if not self.abbr or self.abbr.strip() == "": self.abbr = None
        if not self.indicator_id or self.indicator_id.strip() == "": self.indicator_id = None
        super(Incident, self).save(*args, **kwargs)

    class Meta:
        ordering = ["name"]


class Alias(models.Model):
    """
    Helper class, more or less like a dictionary for alias of Incidents
    """
    incident = models.ForeignKey(Incident, blank=False, null=False)
    name = models.CharField(max_length=100, null=False,blank=False, unique=True)

    def __unicode__(self):
        return "%s - %s" % (self.name, self.incident)

    class Meta:
        verbose_name_plural = "Aliases"

    def save(self, *args, **kwargs):
        if self.name == self.name.lower():
            self.name = self.name.title()

        super(Alias, self).save(*args, **kwargs)

GENDER_CHOICES = (
    ('f', 'Female'),
    ('m', 'Male'),
)

AGE_UNIT_CHOICES = (
    ('y', 'Years'),
    ('m', 'Months'),
    ('w', 'Weeks'),
    ('d', 'Days'),
)

class AgeGroup(models.Model):
    name = models.CharField(max_length=20)
    minimum = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    maximum = models.DecimalField(max_digits=4, decimal_places=1)
    units = models.CharField(max_length=1, choices=AGE_UNIT_CHOICES)

    def __unicode__(self):
        return "%s (%s - %s %s)" % (self.name, self.minimum, self.maximum, self.units)

class Report(models.Model):
    incident = models.ForeignKey(Incident, null=False, blank=False)
    value = models.PositiveSmallIntegerField(null=False, blank=False)
    sex = models.CharField(max_length=1, blank=True, null=True, choices=GENDER_CHOICES)
    age_group = models.ForeignKey(AgeGroup, blank=True, null=True)
    raw_value = models.CharField(max_length=60, null=False, blank=False, editable=False)
    date = models.DateField(default=date.today, blank=False, null=False)
    logged_on = models.DateTimeField(default=datetime.now, blank=False, null=False, editable=False)
    reporter = models.ForeignKey(Contact, blank=True, null=True)
    #Somehow redundant fields but useful for easy and faster reporting
    year = models.PositiveSmallIntegerField(null=False, blank=False, editable=False)
    month = models.PositiveSmallIntegerField(null=False, blank=False, editable=False)
    day = models.PositiveSmallIntegerField(null=False, blank=False, editable=False)
    location = models.ForeignKey(Location, editable=False, limit_choices_to = {'send_live_results':True})
    message = models.ForeignKey(Message, null=True, blank=True, editable=False)
    
    def __unicode__(self):
        return "%s - %s" % (self.incident, self.date)

    def save(self, *args, **kwargs):
        self.year = self.date.year
        self.month = self.date.month
        self.day = self.date.day
        self.location = get_clinic_or_default(self.reporter)
        super(Report, self).save(*args, **kwargs)

    class Meta:
        ordering = ["incident"]

class Separator(models.Model):
    """
    Used to delimit/tokenize disease reports from a message sent. If this model
    is blank a default value will be used in the handlers
    """
    text = models.CharField(max_length=2, unique=True)

    def __unicode__(self):
        return self.text