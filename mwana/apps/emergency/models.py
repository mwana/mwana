# vim: ai ts=4 sts=4 et sw=4
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


class FloodReport(models.Model):
    """A report on flood situation."""

    reported_by = models.ForeignKey(Connection)
    reported_on = models.DateTimeField(default=datetime.datetime.utcnow)
    additional_text = models.CharField(max_length=160, null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES,
                              default="P")
    comments = models.TextField(null=True, blank=True)
    addressed_on = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=160, null=True, blank=True)
    notes = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        contact = self.reported_by.contact.name if self.reported_by.contact \
            else self.reported_by.identity

        location = "Unknown location"
        try:
            location = get_clinic_or_default(self.reported_by.contact)
        except:
            pass

        problem = self.additional_text if self.additional_text else '<NO MORE INFO>'
        return "%s from %s reported '%s' on %s" % (contact, location, problem, self.reported_on)
