# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.locations.models import Location
from django.db import models
from rapidsms.models import Contact


class Client(models.Model):
    GENDER_CHOICES = (
        ('m', 'Male'),
        ('f', 'Female'),
    )
    client_number = models.CharField(max_length=20)
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    mother_name = models.CharField(max_length=50, blank=True, null=True)
    mother_age = models.IntegerField(null=True, blank=True, help_text="Age in years")
    location = models.ForeignKey(Location, related_name='vaccination_client')

    def __unicode__(self):
        return "Client %s. Mother: %s" % (self.client_number, self.mother_name)

    class Meta:
        unique_together = (('client_number', 'location',),)


class VaccinationSession(models.Model):
    SESSION_CHOICES = (
        ('s1', 'session1: BCG Vaccination Session Report'),
        ('s2', 'session2: OPV0 Vaccination Session Report'),
        ('s3', 'session3: OPV1, DPT-HepB-Hib1, PCV1, ROTA1.. Vac. Session Report '),
        ('s4', 'session4: OPV2, DPT-HepB-Hib2, PCV2, ROTA2.. Vac. Session Report '),
        ('s5', 'session5: OPV3, DPT-HepB-Hib3, PCV3, .. Vac. Session Report'),
        ('s6', 'session6: Measles Vaccination Session Report'),
        ('s7', 'session7: OPV4 Vaccination Session Report'),
    )
    session_id = models.CharField(max_length=5, choices=SESSION_CHOICES)
    predecessor = models.ForeignKey('self', null=True, blank=True)
    given_if_not_exist = models.CharField(max_length=5, choices=SESSION_CHOICES)
    min_child_age = models.IntegerField(null=True, blank=True,
        help_text='Minimum days when child should get this vac session. When predecessor'
                  ' exists counting should start from predecessor date. Otherwise, birth date is used')
    max_child_age = models.IntegerField(null=True, blank=True,
        help_text='Maximum days when child should get this vac session. When predecessor'
                  ' exists counting should start from predecessor date. Otherwise, birth date is used')

    def __unicode__(self):
        return self.get_session_id_display()


class Appointment(models.Model):
    client = models.ForeignKey(Client)
    cba_responsible = models.ForeignKey(Contact, limit_choices_to={'types__slug': 'cba'})
    vaccination_session = models.ForeignKey(VaccinationSession)
    scheduled_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)

    def __unicode__(self):
        return "Appointment for %s scheduled for %s. CBA responsible %s" % (self.client, self.scheduled_date, self.cba_responsible)


class SentReminders(models.Model):
    appointment = models.ForeignKey(Appointment)
    date = models.DateTimeField()

    def __unicode__(self):
        return "Reminder for %s sent on %s" % (self.appointment, self.date)


class ReportingTable(models.Model):
    appointment = models.ForeignKey(Appointment)
    reported_visit_date = models.DateField()

    def __unicode__(self):
        return "Vaccination Session report for %s sent on %s" % (self.appointment, self.reported_visit_date)