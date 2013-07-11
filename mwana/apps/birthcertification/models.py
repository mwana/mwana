# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reminders.models import PatientEvent
from datetime import datetime
from mwana.apps.locations.models import Location

from django.db import models
from rapidsms.models import Contact

class SupportedLocation(models.Model):
    """
    Clinics where the birth certication should function
    """

    location = models.ForeignKey(Location, limit_choices_to={'send_live_results':
                              True},
    related_name='cert_supportedlocation')
    supported = models.BooleanField(default=True)

class Agent(models.Model):
    """
    A specialised Contact who can remind parents to go to facility to register
    a birth.
    """

    contact = models.ForeignKey(Contact, limit_choices_to={'types__slug__in':
                              ['cba', 'worker']}, unique=True)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return '%s' % (self.contact.name)


class ActiveAgentManager(models.Manager):
    """
    Filter Agent by which one is active.
    """

    def get_query_set(self):
        return super(ActiveAgentManager, self).get_query_set()\
            .filter(is_active=True)

Agent.add_to_class("active", ActiveAgentManager())

STATUS_CHOICES = (
                  ('nb', 'New birth'),
                  ('regremindersent', 'Reminder to register birth sent'),
                  ('registered', 'Birth registered at Facility'),
                  ('ready', 'Certificate sent to Clinic'),
                  ('notified', 'Reminder to get Certificate sent'),
                  ('collected', 'Parents collected certificate'),
)

class Certification(models.Model):
    birth = models.ForeignKey(PatientEvent, unique=True)
    reg_notification_date = models.DateTimeField(blank=True, null=True, editable=False)
    registration_date = models.DateField(blank=True, null=True)
    certificate_sent_to_clinic = models.DateField(blank=True, null=True)
    certificate_notification_date = models.DateField(blank=True, null=True, editable=False, verbose_name='cert. notification date')
    parents_got_certificate = models.DateField(blank=True, null=True)
    certificate_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    status = models.CharField(max_length=15, default='nb', choices=STATUS_CHOICES, editable=False)

    def save(self, *args, **kwargs):

        if self.parents_got_certificate:
            self.status = 'collected'
        elif self.certificate_notification_date:
            self.status = 'notified'
        elif self.certificate_sent_to_clinic:
            self.status = 'ready'
        elif self.registration_date:
            self.status = 'registered'
        elif self.reg_notification_date:
            self.status = 'regremindersent'

        super(Certification, self).save(*args, **kwargs)

    def __unicode__(self):
        return 'Certification for %s' % (self.birth)


#SCHEDULE_TYPES = (
#    ('BR','Birth Registration'),
#)
#
#class Schedule(models.Model):
#    days = models.PositiveIntegerField(default=0)# after how many days(minimum) after a new birth should this appointment be
#    type = models.CharField(max_length=5, choices=SCHEDULE_TYPES)
#
#    def __unicode__(self):
#        return "%s day schedule"


class RegistrationReminder(models.Model):
    """
    Reminder to register a birth at the facility. Don't confuse this with RemindMI
    birth registration. This registration is registration with civil authorites
    so that a birth certicate can be issued
    """
    certification = models.ForeignKey(Certification)
    agent = models.ForeignKey(Agent)
    date_sent = models.DateTimeField(default=datetime.now, editable=False)

    def __unicode__(self):
        return "Reminder sent to %s to regisiter %s." % (self.agent, self.certification)


class CertificateNotification(models.Model):
    """
    Notication that certificate is ready for collection at clinic
    """
    certification = models.ForeignKey(Certification)
    agent = models.ForeignKey(Agent)
    date_sent = models.DateTimeField(default=datetime.now, editable=False)

    def __unicode__(self):
        return "Reminder to collect certificate for %s" % (self.certification)