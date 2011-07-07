# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime

from django.db import models
from mwana.apps.locations.models import Location
from rapidsms.models import Contact


class SMSAlertLocation(models.Model):
    """
    Manages facilities that can receive SMS alerts
    """
    district = models.ForeignKey(Location, limit_choices_to={"type__slug":"districts"})
    enabled = models.BooleanField(default=False)
    
    def __str__(self):
        return "%s: %s" % (self.district.name, "Enabled" if self.enabled else "Not Enabled")
    
class Hub(models.Model):
    name = models.CharField(max_length=50)
    district = models.ForeignKey(Location, unique=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return "%s in %s district. Contact: %s" % (self.name,
                                                   self.district.name,
                                                   self.phone)
class Lab(models.Model):
    source_key = models.CharField(max_length=50)
    name = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return "%s. %s . Contact: %s" % (self.source_key, self.name, self.phone)

class DhoSMSAlertNotification(models.Model):
    """
    Records alerts sent to DHO staff
    """
    REPORT_TYPES = (
                    ('M', 'Monthly Alert'),
                    ('W', 'Weekly Alert'),
                    )
    ALERT_TYPES = (
                   ("1", "DISTRICT_NOT_SENDING_DBS"),
                   ("2", "LONG_PENDING_RESULTS"),
                   ("3", "CLINIC_NOT_USING_SYSTEM"),
                   ("4", "LAB_NOT_PROCESSING_DBS"),
                   ("5", "LAB_NOT_SENDING_PAYLOD"),
                   ("6", "CLINIC_NOT_USING_TRACE"),
                   )

    contact  = models.ForeignKey(Contact, blank=True, null=True)
    district = models.ForeignKey(Location)
    report_type    = models.CharField(choices=REPORT_TYPES, max_length=1, blank=True)
    alert_type    = models.CharField(choices=ALERT_TYPES, max_length=1, blank=True)
    date_sent     = models.DateTimeField(default=datetime.now)