# vim: ai ts=4 sts=4 et sw=4
from mwana.const import CLINIC_SLUGS
from mwana.apps.reports.utils.htmlhelper import get_month_end
from django.db import models
from mwana.apps.locations.models import Location
from django.conf import settings
from rapidsms.models import Contact
from datetime import datetime
from django.contrib.auth.models import User
from datetime import date


class Turnaround(models.Model):
    """
    A stub to display a view in django admin format for turnaround data
    """
    province = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    facility = models.CharField(max_length=100)
    facility_id = models.IntegerField()
    facility_slug = models.CharField(max_length=10)
    transporting = models.IntegerField(blank=True, null=True)
    processing = models.IntegerField(blank=True, null=True)
    delays = models.IntegerField(blank=True, null=True, verbose_name="Entering Time")
    retrieving = models.IntegerField(blank=True, null=True)
    turnaround = models.IntegerField(blank=True, null=True)
    collected_on = models.DateField(blank=True, null=True)
    received_at_lab = models.DateField(blank=True, null=True)
    processed_on = models.DateField(blank=True, null=True)
    date_reached_moh = models.DateField(blank=True, null=True)
    date_retrieved = models.DateField(blank=True, null=True)
    lab = models.CharField(max_length=100)
    result = models.CharField(max_length=100)
    sample_id = models.CharField(max_length=100)
    requisition_id = models.CharField(max_length=100)


class LabtestsTurnaround(models.Model):
    """
    A stub to display a view in django admin format for turnaround data
    """
    province = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    facility = models.CharField(max_length=100)
    facility_id = models.IntegerField()
    facility_slug = models.CharField(max_length=10)
    transporting = models.IntegerField(blank=True, null=True)
    processing = models.IntegerField(blank=True, null=True)
    delays = models.IntegerField(blank=True, null=True, verbose_name="Entering Time")
    retrieving = models.IntegerField(blank=True, null=True)
    turnaround = models.IntegerField(blank=True, null=True)
    collected_on = models.DateField(blank=True, null=True)
    received_at_lab = models.DateField(blank=True, null=True)
    processed_on = models.DateField(blank=True, null=True)
    date_reached_moh = models.DateField(blank=True, null=True)
    date_retrieved = models.DateField(blank=True, null=True)
    lab = models.CharField(max_length=100)


class ResultsForFollowup(models.Model):
    """
    A stub to display a view in django admin format for results that need
    patient follow up
    """
    province = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    facility = models.CharField(max_length=100)
    facility_id = models.IntegerField(null=True, blank=True)
    lab_id = models.CharField(max_length=20) 
    requisition_id = models.CharField(max_length=50)    
    birthdate = models.DateField(null=True, blank=True)
    child_age = models.IntegerField(null=True, blank=True)
    child_age_unit = models.CharField(null=True, blank=True, max_length=20)
    sex = models.CharField( max_length=1, blank=True)
    collecting_health_worker = models.CharField(max_length=100, blank=True)
    verified = models.NullBooleanField(null=True, blank=True)
    result = models.CharField(max_length=1, blank=True)
    collected_on = models.DateField(blank=True, null=True)
    received_at_lab = models.DateField(blank=True, null=True)
    processed_on = models.DateField(blank=True, null=True)
    date_reached_moh = models.DateField(blank=True, null=True)
    date_retrieved = models.DateField(blank=True, null=True)
    lab = models.CharField(max_length=100)
    result_detail = models.CharField(max_length=200, blank=True)  # reason for rejection or explanation of inconsistency

    def __unicode__(self):
        return "%s: %s" % (self.requisition_id, self.result)


class SupportedLocation(models.Model):
    location = models.ForeignKey(Location)
    supported = models.BooleanField(default=True)

    def __unicode__(self):
        return "%s %s" % (self.location.name, "supported" if self.supported else "Not supported")


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
        ('M', 'Monthly Report'),
    )

    contact = models.ForeignKey(Contact, related_name='dho')
    district = models.ForeignKey(Location)
    type = models.CharField(choices=REPORT_TYPES, max_length=1, blank=True)
    samples = models.PositiveIntegerField()
    results = models.PositiveIntegerField()
    births = models.PositiveIntegerField()
    date = models.DateField()
    date_sent = models.DateTimeField(default=datetime.now)

    def __unicode__(self):
        return "%s DHO EID & Births Summary for %s on %s" % \
               (self.district.name, self.date, self.date_sent.date())


class PhoReportNotification(models.Model):
    """
    Records EID and Birth reports sent to pho
    """
    REPORT_TYPES = (
        ('M', 'Monthly Report'),
    )

    contact = models.ForeignKey(Contact, related_name='pho')
    province = models.ForeignKey(Location)
    type = models.CharField(choices=REPORT_TYPES, max_length=1, blank=True)
    samples = models.PositiveIntegerField()
    results = models.PositiveIntegerField()
    births = models.PositiveIntegerField()
    date = models.DateField()
    date_sent = models.DateTimeField(default=datetime.now)

    def __unicode__(self):
        return "%s DHO EID & Births Summary for %s on %s" % \
               (self.province.name, self.date, self.date_sent.date())


class CbaThanksNotification(models.Model):
    """
    Send thank you messages to CBA's who registered births during a given month
    """
    REPORT_TYPES = (
        ('M', 'Monthly Report'),
    )

    contact = models.ForeignKey(Contact, related_name='cba')
    facility = models.ForeignKey(Location)
    type = models.CharField(choices=REPORT_TYPES, max_length=1, blank=True)
    births = models.PositiveIntegerField()
    date = models.DateField()
    date_sent = models.DateTimeField(default=datetime.now)

    def __unicode__(self):
        return "Congratulatory message for %s of %s for registering %s births in %s" % \
               (self.contact.name, self.facility.name, self.births, self.date)


class CbaEncouragement(models.Model):
    """
    Send encouragement/reminder messages to CBA's to register births
    """
    REPORT_TYPES = (
        ('M', 'Monthly Encouragement'),
    )

    contact = models.ForeignKey(Contact)
    facility = models.ForeignKey(Location)
    type = models.CharField(choices=REPORT_TYPES, max_length=1, blank=True)
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
    """
    Reporting table.
    """
    count = models.PositiveIntegerField()
    province = models.CharField(max_length=30, null=True, blank=True)
    district = models.CharField(max_length=30, null=True, blank=True)
    facility = models.CharField(max_length=50, null=True, blank=True)
    worker_type = models.CharField(max_length=30)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    province_slug = models.CharField(max_length=6, null=True, blank=True)
    district_slug = models.CharField(max_length=6, null=True, blank=True)
    facility_slug = models.CharField(max_length=10, null=True, blank=True)
    absolute_location = models.ForeignKey(Location)
    min_date = models.DateField(null=True, blank=True)
    max_date = models.DateField(null=True, blank=True)
    month_year = models.CharField(max_length=8, null=True, blank=True)
    count_incoming = models.PositiveIntegerField(default=0, null=True, blank=True)
    count_outgoing = models.PositiveIntegerField(default=0, null=True, blank=True)

    def save(self, *args, **kwargs):
        my_date = date(self.year, self.month, 1)
        if not self.min_date:
            self.min_date = my_date
        if not self.max_date:
            self.max_date = get_month_end(my_date)
        if not self.month_year:
            self.month_year = my_date.strftime('%b %Y')
        super(MessageByLocationByUserType, self).save(*args, **kwargs)

    class Meta:
        unique_together = ("absolute_location", "year", "month", "worker_type")


class MessageByLocationByBackend(models.Model):
    """
    Reporting table.
    """
    count = models.PositiveIntegerField()
    province = models.CharField(max_length=30, null=True, blank=True)
    district = models.CharField(max_length=30, null=True, blank=True)
    facility = models.CharField(max_length=50, null=True, blank=True)
    backend = models.CharField(max_length=30)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    province_slug = models.CharField(max_length=6, null=True, blank=True)
    district_slug = models.CharField(max_length=6, null=True, blank=True)
    facility_slug = models.CharField(max_length=10, null=True, blank=True)
    absolute_location = models.ForeignKey(Location, null=True, blank=True)
    min_date = models.DateField(null=True, blank=True)
    max_date = models.DateField(null=True, blank=True)
    month_year = models.CharField(max_length=8, null=True, blank=True)
    count_incoming = models.PositiveIntegerField(default=0, null=True, blank=True)
    count_outgoing = models.PositiveIntegerField(default=0, null=True, blank=True)

    def save(self, *args, **kwargs):
        my_date = date(self.year, self.month, 1)
        if not self.min_date:
            self.min_date = my_date
        if not self.max_date:
            self.max_date = get_month_end(my_date)
        if not self.month_year:
            self.month_year = my_date.strftime('%b %Y')
        super(MessageByLocationByBackend, self).save(*args, **kwargs)


class MessageByLocationUserTypeBackend(models.Model):
    """
    Reporting table.
    """
    count = models.PositiveIntegerField()
    province = models.CharField(max_length=30, null=True, blank=True)
    district = models.CharField(max_length=30, null=True, blank=True)
    facility = models.CharField(max_length=50, null=True, blank=True)
    backend = models.CharField(max_length=30)
    worker_type = models.CharField(max_length=30, null=True, blank=True)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    province_slug = models.CharField(max_length=6, null=True, blank=True)
    district_slug = models.CharField(max_length=6, null=True, blank=True)
    facility_slug = models.CharField(max_length=10, null=True, blank=True)
    absolute_location = models.ForeignKey(Location, null=True, blank=True)
    min_date = models.DateField(null=True, blank=True)
    max_date = models.DateField(null=True, blank=True)
    month_year = models.CharField(max_length=8, null=True, blank=True)
    count_incoming = models.PositiveIntegerField(default=0, null=True, blank=True)
    count_outgoing = models.PositiveIntegerField(default=0, null=True, blank=True)
    count_DBS_notification = models.PositiveIntegerField(default=0, null=True, blank=True)
    count_dbs2_notification = models.PositiveIntegerField(default=0, null=True, blank=True)# tdrc
    count_vl_notification = models.PositiveIntegerField(default=0, null=True, blank=True)
    count_participant_notification = models.PositiveIntegerField(default=0, null=True, blank=True)

    def save(self, *args, **kwargs):
        my_date = date(self.year, self.month, 1)
        if not self.min_date:
            self.min_date = my_date
        if not self.max_date:
            self.max_date = get_month_end(my_date)
        if not self.month_year:
            self.month_year = my_date.strftime('%b %Y')
        super(MessageByLocationUserTypeBackend, self).save(*args, **kwargs)

#    class Meta:
#        unique_together=("absolute_location", "year", "month", "backend")


class MsgByLocationByBackendBuildLog(models.Model):
    message_id = models.IntegerField(null=True, blank=True, editable=False, default=0)
    lock = models.IntegerField(unique=True)

    def __unicode__(self):
        return "%s" % self.message_id

    def save(self, *args, **kwargs):
        if self.lock and self.lock != 1:
            return
        super(MsgByLocationByBackendBuildLog, self).save(*args, **kwargs)


class MsgByLocationUserTypeBackendLog(models.Model):
    message_id = models.IntegerField(editable=False, default=0)
    locked = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s" % self.message_id


class ScaleUpSite(models.Model):
    """
    Reporting table.
    """
    province = models.CharField(max_length=30, null=True, blank=True, editable=False)
    district = models.CharField(max_length=30, null=True, blank=True, editable=False)
    site = models.ForeignKey(Location, limit_choices_to={"type__slug__in": list(CLINIC_SLUGS)}, unique=True, verbose_name='Facility')
    PMTCT = models.NullBooleanField()
    EID = models.NullBooleanField()
    ART = models.NullBooleanField()
    PaedsART = models.NullBooleanField()
    Mwana = models.NullBooleanField(editable=False)
    ActiveOnMwana = models.NullBooleanField(editable=False, verbose_name='Sending DBS Samples')

    def __unicode__(self):
        return "%s" % self.site

    def save(self, *args, **kwargs):
        if self.site and self.district is None:
            self.district = self.site.parent.name
        if self.site and self.province is None:
            self.province = self.site.parent.parent.name
        if self.site and not self.Mwana == True:
            self.Mwana = SupportedLocation.objects.filter(location=self.site, supported=True).exists()
        if (self.ActiveOnMwana or self.Mwana) and not self.PaedsART == True:
            self.PaedsART = True
        if (self.ActiveOnMwana or self.Mwana) and not self.EID == True:
            self.EID = True
        super(ScaleUpSite, self).save(*args, **kwargs)


class ClinicsNotSendingDBS(models.Model):
    """
   Alerts Reporting table.
    """
    location = models.ForeignKey(Location, limit_choices_to={"type__slug__in": list(CLINIC_SLUGS)}, unique=True)
    last_sent_samples = models.PositiveSmallIntegerField(blank=True, null=True)# how many days ago
    last_retrieved_results = models.PositiveSmallIntegerField(blank=True, null=True)# how many days ago
    last_used_sent = models.PositiveSmallIntegerField(blank=True, null=True)
    last_used_check = models.PositiveSmallIntegerField(blank=True, null=True)
    last_used_result = models.PositiveSmallIntegerField(blank=True, null=True)
    last_used_trace = models.PositiveSmallIntegerField(blank=True, null=True)# how many days ago
    last_modified = models.DateTimeField(auto_now=True)
    contacts = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "location=%s, last_sent_samples=%s, last_retrieved_results=%s, last_used_sent=%s, last_used_check=%s, last_used_result=%s, last_used_trace=%s, last_modified=%s" %(self.location, self.last_sent_samples, self.last_retrieved_results, self.last_used_sent, self.last_used_check, self.last_used_result, self.last_used_trace, self.last_modified)

    class Meta:
        verbose_name_plural = "Clinics Not Sending DBS Alerts"

class Coverage(models.Model):
    location = models.ForeignKey(Location, limit_choices_to={"type__slug__in": list(CLINIC_SLUGS)}, unique=True, null=True, blank=True)
    raw_district_text = models.CharField(max_length=50)
    raw_facility_text = models.CharField(max_length=100)
    supported = models.NullBooleanField()
    number_of_active_staff = models.PositiveIntegerField(null=True, blank=True)
    number_of_active_cba = models.PositiveIntegerField(null=True, blank=True)
    matched = models.BooleanField(default=False)
    site_category = models.CharField(max_length=100, null=True, blank=True)
    district_category = models.CharField(max_length=100, null=True, blank=True)
    partner = models.CharField(max_length=100, null=True, blank=True)


    def __unicode__(self):
        return "%s" % self.raw_facility_text

    def save(self, *args, **kwargs):
        self.matched = bool(self.location)
        super(Coverage, self).save(*args, **kwargs)

    class Meta:
        unique_together = ("raw_district_text", "raw_facility_text")
