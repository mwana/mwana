# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.utils.htmlhelper import get_month_end
from django.db import models
from mwana.apps.locations.models import Location
#from rapidsms.models import Connection
from rapidsms.models import Contact
from datetime import datetime
from django.contrib.auth.models import User
from datetime import date

class Turnaround(models.Model):
    """
    A stub to display a view in django admin format for turnaround data
    """
    district = models.CharField(max_length=50)
    facility = models.CharField(max_length=100)
    transporting = models.IntegerField(blank=True, null=True)
    processing = models.IntegerField(blank=True, null=True)
    delays = models.IntegerField(blank=True, null=True, verbose_name="Entering Time")
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

class DhoReportNotification(models.Model):
    """
    Records EID and Birth reports sent to dho
    """
    REPORT_TYPES = (
    ('M','Monthly Report'),
    )

    contact  = models.ForeignKey(Contact, related_name='dho')
    district = models.ForeignKey(Location)
    type    = models.CharField(choices=REPORT_TYPES, max_length=1, blank=True)
    samples = models.PositiveIntegerField()
    results = models.PositiveIntegerField()
    births = models.PositiveIntegerField()
    date     = models.DateField()
    date_sent     = models.DateTimeField(default=datetime.now)


    def __unicode__(self):
        return "%s DHO EID & Births Summary for %s on %s" % \
            (self.district.name, self.date, self.date_sent.date())

class PhoReportNotification(models.Model):
    """
    Records EID and Birth reports sent to pho
    """
    REPORT_TYPES = (
    ('M','Monthly Report'),
    )

    contact  = models.ForeignKey(Contact, related_name='pho')
    province = models.ForeignKey(Location)
    type    = models.CharField(choices=REPORT_TYPES, max_length=1, blank=True)
    samples = models.PositiveIntegerField()
    results = models.PositiveIntegerField()
    births = models.PositiveIntegerField()
    date     = models.DateField()
    date_sent     = models.DateTimeField(default=datetime.now)


    def __unicode__(self):
        return "%s DHO EID & Births Summary for %s on %s" % \
            (self.province.name, self.date, self.date_sent.date())

class CbaThanksNotification(models.Model):
    """
    Send thank you messages to CBA's who registered births during a given month
    """
    REPORT_TYPES = (
    ('M','Monthly Report'),
    )

    contact  = models.ForeignKey(Contact, related_name='cba')
    facility = models.ForeignKey(Location)
    type  = models.CharField(choices=REPORT_TYPES, max_length=1, blank=True)
    births = models.PositiveIntegerField()
    date  = models.DateField()
    date_sent = models.DateTimeField(default=datetime.now)


    def __unicode__(self):
        return "Congratulatory message for %s of %s for registering %s births in %s" % \
            (self.contact.name, self.facility.name, self.births, self.date)

class CbaEncouragement(models.Model):
    """
    Send encouragement/reminder messages to CBA's to register births
    """
    REPORT_TYPES = (
    ('M','Monthly Encouragement'),
    )

    contact  = models.ForeignKey(Contact)
    facility = models.ForeignKey(Location)
    type  = models.CharField(choices=REPORT_TYPES, max_length=1, blank=True)
    date_sent = models.DateTimeField(default=datetime.now)


    def __unicode__(self):
        return "Encouragement message to %s to register births" % \
            (self.contact.name)

class Login(models.Model):
    user = models.ForeignKey(User)
    ever_logged_in = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s: Ever logged in? %s" % (self.user, "Yes" if self.ever_logged_in else "No")


class MessageByLocationByUserType(models.Model):
    count = models.PositiveIntegerField()
    province = models.CharField(max_length=30, null=True, blank=True)
    district = models.CharField(max_length=30, null=True, blank=True)
    facility = models.CharField(max_length=50, null=True, blank=True)
    worker_type = models.CharField(max_length=30)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    province_slug = models.CharField(max_length=6, null=True, blank=True)
    district_slug = models.CharField(max_length=6, null=True, blank=True)
    facility_slug = models.CharField(max_length=6, null=True, blank=True)
    absolute_location = models.ForeignKey(Location)
    min_date = models.DateField(null=True, blank=True)
    max_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        my_date = date(self.year, self.month, 1)
        if not self.min_date:
            self.min_date = my_date
        if not self.max_date:
            self.max_date = get_month_end(my_date)
        super(MessageByLocationByUserType, self).save(*args, **kwargs)

    class Meta:
        unique_together=("absolute_location", "year", "month", "worker_type")