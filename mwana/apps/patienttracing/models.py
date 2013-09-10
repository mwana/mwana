# vim: ai ts=4 sts=4 et sw=4
import datetime

from django.db import models
from rapidsms.models import Contact
from mwana.apps.reminders.models import PatientEvent
from mwana.apps.locations.models import Location


class SentConfirmationMessage(models.Model):
    patient_name = models.CharField(max_length=50)
    initiator_contact = models.ForeignKey(Contact, limit_choices_to={'types__slug': 'worker'},
                                     related_name='trace_confirmation_initiator',
                                     null=True, blank=True)
    cba_contact = models.ForeignKey(Contact, limit_choices_to={'types__slug': 'cba'},
                                    related_name='trace_confirmation_cba')
    message = models.CharField(max_length=160)
    sent_date = models.DateTimeField()
    
    
class PatientTrace(models.Model):
    STATUS_CHOICES = (
                  ("new", "New"),
                  ("told", "Told"),
                  ("confirmed", "Confirmed"),
                  ("awaiting_confirm", "Awaiting confirm"), #waiting for CBA to send in confirm message (after system sent confirm reminder msg)
                  ("refused", "Patient refused"),# when mother can't be traced
                  ("lost", "Lost to followup"),# when mother can't be traced
                  ("dead", "Patient died"),# when mother can't be traced
                  )

    TYPE_CHOICES = (
                ("manual", "Manual"),
                ("6 day", "6 day"),
                ("6 week", "6 week"),
                ("6 month","6 month"),
                ("unrecognized_patient", "Unrecognized Patient")  #this is when we get a told message and are unable to link it to a previously initiated trace.
                )

    INITIATOR_CHOICES = (
                         ("admin", "Admin"),
                         ("clinic_worker", "Clinic worker"),
                         ("automated_task", "Sytem Initiated"),
                         ("cba", "CBA"),
                         )

    initiator = models.CharField(choices=INITIATOR_CHOICES, max_length=20)
    
    # person who initiates the tracing (used when initiator=clinic_worker)
    initiator_contact = models.ForeignKey(Contact, related_name='patients_traced',
                                     limit_choices_to={'types__slug': 'clinic_worker'},
                                     null=True, blank=True)
    clinic = models.ForeignKey(Location, related_name='patient_location', null=True, blank=True)
    type = models.CharField(choices=TYPE_CHOICES, max_length=30)
    name = models.CharField(max_length=50) # name of patient to trace
#    reason = models.CharField(max_length=90) #optional reason for why the trace was initiated
    patient_event = models.ForeignKey(PatientEvent, related_name='patient_traces',
                                      null=True, blank=True) 
    messenger = models.ForeignKey(Contact,  related_name='patients_reminded',
                            limit_choices_to={'types__slug': 'cba'}, null=True,
                            blank=True)# cba who informs patient

    confirmed_by = models.ForeignKey(Contact, related_name='patient_traces_confirmed',
                            limit_choices_to={'types__slug': 'cba'}, null=True,
                            blank=True)# cba who confirms that patient visited clinic

    status = models.CharField(choices=STATUS_CHOICES, max_length=25) # status of tracing activity

    start_date = models.DateTimeField() # date when tracing starts
    reminded_date = models.DateTimeField(null=True, blank=True) # date when cba tells mother
    confirmed_date = models.DateTimeField(null=True, blank=True)# date of confirmation that patient visited clinic   
    

    def save(self, * args, ** kwargs):
        if not self.pk:
            self.start_date = datetime.datetime.now()
            self.name = self.name.strip().title()
        super(PatientTrace, self).save(*args, ** kwargs)

    def __unicode__(self):
        return "%s patient trace for %s" % (self.get_initiator_display(), self.name)

def get_status_new():
    return PatientTrace.STATUS_CHOICES[0][0]

def get_status_told():
    return PatientTrace.STATUS_CHOICES[1][0]

def get_status_await_confirm():
    return PatientTrace.STATUS_CHOICES[3][0]

def get_status_confirmed():
    return PatientTrace.STATUS_CHOICES[2][0]

def get_initiator_cba():
    return PatientTrace.INITIATOR_CHOICES[3][0]

def get_initiator_clinic_worker():
    return PatientTrace.INITIATOR_CHOICES[1][0]

def get_initiator_automated():
    return PatientTrace.INITIATOR_CHOICES[2][0]

def get_initiator_admin():
    return PatientTrace.INITIATOR_CHOICES[0][0]

def get_type_manual():
    return PatientTrace.TYPE_CHOICES[0][0]

def get_type_6day():
    return PatientTrace.TYPE_CHOICES[1][0]
def get_type_6week():
    return PatientTrace.TYPE_CHOICES[2][0]
def get_type_6month():
    return PatientTrace.TYPE_CHOICES[3][0]
def get_type_unrecognized():
    return PatientTrace.TYPE_CHOICES[4][0]


class CorrectedTrace(models.Model):
    copied_from = models.ForeignKey(PatientTrace, related_name="source_patient_trace")
    copied_to = models.ForeignKey(PatientTrace)

    def __unicode__(self):
        return "Source: %s. Destination: %s" % (self.copied_from, self.copied_to)