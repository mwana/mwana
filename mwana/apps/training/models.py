# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.webreports.models import ReportingGroup
from mwana.apps.contactsplus.models import ContactType
from django.db import models
from rapidsms.models import Contact
from mwana.apps.locations.models import Location
import datetime
# Create your models here.

class TrainingSession(models.Model):
    start_date = models.DateTimeField(default=datetime.datetime.utcnow)
    end_date = models.DateTimeField(blank=True, null=True)
    trainer = models.ForeignKey(Contact)
    is_on = models.BooleanField(default=True)
    location = models.ForeignKey(Location)

    def __unicode__(self):
        return 'Training on %s by %s at %s' % (self.start_date, self.trainer, self.location)

class Trained(models.Model):
    """
    Keeps a record of those that have been trained
    """
    name = models.CharField(max_length=50, null=False, blank=False)
    phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.CharField(max_length=50, null=True, blank=True)
    location = models.ForeignKey(Location)
    type = models.ForeignKey(ContactType)#,
#    limit_choices_to={'slug__in':(type.slug for type in ContactType.objects.exclude(name__in=["Patient", "DBS Printer"]))})
    trained_by = models.ForeignKey(ReportingGroup, blank=True, null=True)
    date = models.DateField(default=datetime.date.today, blank=True, null=True)
    additional_text = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return '%s of %s trained on %s by %s' % (self.name, self.location, self.date, self.trained_by )

    def save(self, *args, **kwargs):
        if not self.email or self.email.trim() == '':  self.email = None
        super(Trained, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Trained People"