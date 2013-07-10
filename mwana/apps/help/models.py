# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.webreports.models import ReportingGroup
from rapidsms.models import Contact
from django.db import models
from rapidsms.models import Connection
import datetime
from mwana.util import get_clinic_or_default

STATUS_CHOICES = (
    ("P", "pending"),
    ("A", "active"),
    ("R", "resolved"),
    ("C", "closed"),
)

class HelpRequest(models.Model):
    """A request for help"""
    
    requested_by = models.ForeignKey(Connection)
    requested_on = models.DateTimeField(default=datetime.datetime.utcnow)
    additional_text = models.CharField(max_length=160, null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="P")
    addressed_on = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=160, null=True, blank=True)
    notes = models.CharField(max_length=255, null=True, blank=True)
    
    def __unicode__(self):
        contact = self.requested_by.contact.name if self.requested_by.contact \
                    else self.requested_by.identity

        location = "Unknown location"
        try:
            location = get_clinic_or_default(self.requested_by.contact)
        except:
            pass

        problem = self.additional_text if self.additional_text else '<NO MORE INFO>'
        return "%s from %s asks for help with '%s' on %s"  % (contact, location, problem, self.requested_on)


class HelpAdminGroup(models.Model):
    contact = models.ForeignKey(Contact, limit_choices_to={"is_help_admin": True, "is_active": True})
    group = models.ForeignKey(ReportingGroup)

    def __unicode__(self):
        return "%s: %s" % (self.contact, self.group)