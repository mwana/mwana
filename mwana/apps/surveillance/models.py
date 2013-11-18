# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.webreports.models import ReportingGroup
from django.contrib.auth.models import User
from mwana.apps.broadcast.models import BroadcastMessage
from rapidsms.contrib.messagelog.models import Message
from mwana.apps.locations.models import Location
from django.db import models
from datetime import datetime
from datetime import date
from datetime import timedelta
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
    lowered_name = models.CharField(max_length=100, null=False, blank=False, unique=True)
    indicator_id = models.CharField(max_length=8, null=True, blank=True, unique=True)
    abbr = models.CharField(max_length=8, null=True, blank=True)
    type = models.CharField(max_length=3, choices=INCIDENT_TYPES, default='dis')
    
    def __unicode__(self):
        if self.indicator_id:
            return "%s: %s" % (self.indicator_id, self.name)
        return self.name

    def save(self, *args, **kwargs):
        self.lowered_name = self.name.lower()
        if self.name == self.name.lower():
            self.name = self.name.title()
        if not self.abbr or self.abbr.strip() == "": self.abbr = None
        if not self.indicator_id or self.indicator_id.strip() == "": self.indicator_id = None
        super(Incident, self).save(*args, **kwargs)
        Alias.create_alias(self, self.name)
        if self.abbr:
            Alias.create_alias(self, self.abbr)
        if self.indicator_id:
            Alias.create_alias(self, self.indicator_id)
        if self.indicator_id:
            Alias.create_alias(self, self.indicator_id.replace('-', ''))

    class Meta:
        ordering = ["name"]


class Alias(models.Model):
    """
    Helper class, more or less like a dictionary for alias of Incidents
    """
    incident = models.ForeignKey(Incident, blank=False, null=False)
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)

    @classmethod
    def create_alias(cls, incident, name):
        if not Alias.objects.filter(incident=incident, name__iexact=name):
            Alias.objects.create(incident=incident, name=name)

    def __unicode__(self):
        return "%s - %s" % (self.name, self.incident)

    class Meta:
        verbose_name_plural = "Aliases"

    def save(self, *args, **kwargs):
        if Alias.objects.filter(incident=self.incident, name__iexact=self.name):
            return
        if self.name == self.name.lower():
            self.name = self.name.title()

        super(Alias, self).save(*args, **kwargs)

    class Meta:
        ordering = ["incident"]
        verbose_name = "Incident Alias"
        verbose_name_plural = "Incident Aliases"

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


class Source(models.Model):
    message = models.ForeignKey(Message, null=True, blank=True, editable=False)
    parsed = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    logged_on = models.DateTimeField(default=datetime.now, blank=False, null=False, editable=False)

    def __unicode__(self):
        return "%s. %s" % (self.parsed, self.message)


class Report(models.Model):
    incident = models.ForeignKey(Incident, null=False, blank=False)
    value = models.PositiveSmallIntegerField(null=False, blank=False)
    sex = models.CharField(max_length=1, blank=True, null=True, choices=GENDER_CHOICES)
    age_group = models.ForeignKey(AgeGroup, blank=True, null=True)
    raw_value = models.CharField(max_length=120, null=False, blank=False, editable=False)
    date = models.DateField(blank=False, null=False)
    reporter = models.ForeignKey(Contact, blank=True, null=True)
    #Somehow redundant fields but useful for easy and faster reporting
    week_of_year = models.PositiveSmallIntegerField(null=False, blank=False, editable=False)# does not use isocalendar
    year = models.PositiveSmallIntegerField(null=False, blank=False, editable=False)
    month = models.PositiveSmallIntegerField(null=False, blank=False, editable=False)
    day = models.PositiveSmallIntegerField(null=False, blank=False, editable=False)
    location = models.ForeignKey(Location, editable=False, limit_choices_to = {'send_live_results':True})
    source = models.ForeignKey(Source, null=True, blank=True, editable=False)
    
    def __unicode__(self):
        return "%s - %s" % (self.incident, self.date)

    def save(self, *args, **kwargs):
        
        self.location = get_clinic_or_default(self.reporter)
        if not self.date and not self.week_of_year:
            self.date = date.today()
            self.week_of_year = int(self.date.strftime('%U'))
        elif self.date and not self.week_of_year:
            self.week_of_year = int(self.date.strftime('%U'))
        elif self.week_of_year and not self.date:
            today = date.today()
            this_jan = date(today.year, 1, 1)
            days_ago = (today - this_jan).days
            for i in range(days_ago):
                if int((today - timedelta(days=i)).strftime('%U')) == self.week_of_year :
                    self.date = today - timedelta(days=i)
                    break
        self.year = self.date.year
        self.month = self.date.month
        self.day = self.date.day
        if Report.objects.filter(date=self.date, incident=self.incident, value=self.value, location=self.location):
            return
        super(Report, self).save(*args, **kwargs)

    class Meta:
        ordering = ["incident"]
        verbose_name = "Incident Report"

class Separator(models.Model):
    """
    Used to delimit/tokenize disease reports from a message sent. If this model
    is blank a default value will be used in the handlers
    """
    text = models.CharField(max_length=2, unique=True)

    def __unicode__(self):
        return self.text


class ImportedReport(models.Model):
    source_message = models.ForeignKey(BroadcastMessage)
    report = models.ForeignKey(Report, null=True, blank=True)
    unparsed = models.CharField(max_length=500, null=True, blank=True)

    def __unicode__(self):
        return "%s => %s" % (self.source_message.text[:100], self.report)


class UserIncident(models.Model):
    """
    Web user can decide what 'indicators' they want to view apart from those
    defined at group level
    """
    user = models.ForeignKey(User)
    incident = models.ForeignKey(Incident)

    def __unicode__(self):
        return "%s: %s" % (self.user, self.incident)

    class Meta:
        unique_together = (('user', 'incident',),)


class GroupIncident(models.Model):
    group = models.ForeignKey(ReportingGroup)
    incident = models.ForeignKey(Incident)

    def __unicode__(self):
        return "%s: %s" % (self.group, self.incident)

    class Meta:
        unique_together = (('group', 'incident',),)
