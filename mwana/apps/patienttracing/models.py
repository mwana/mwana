# vim: ai ts=4 sts=4 et sw=4
import datetime

from django.db import models
from rapidsms.models import Contact
from mwana.apps.reminders.models import PatientEvent
from mwana.apps.locations.models import Location


class SentConfirmationMessage(models.Model):
    patient_name = models.CharField(max_length=50)
    initiator_contact = models.ForeignKey(
        Contact, limit_choices_to={'types__slug': 'worker'},
        related_name='trace_confirmation_initiator',
        null=True, blank=True)
    cba_contact = models.ForeignKey(
        Contact, limit_choices_to={'types__slug': 'cba'},
        related_name='trace_confirmation_cba')
    message = models.CharField(max_length=160)
    sent_date = models.DateTimeField()


class PatientTrace(models.Model):
    STATUS_CHOICES = (
        ("new", "New"),
        ("told", "Told"),
        ("confirmed", "Confirmed"),
        # ("awaiting_confirm", "awaiting_confirm"),  # from hsa
        ("found", "Found"),  # from hsa
        ("refused", "Refused"),  # found not returning
        ("lost", "Lost"),  # not found
        ("trans", "Moved"),  # patient transfered
        ("dead", "Dead"),  # patient died
    )

    TYPE_CHOICES = (
        ("manual", "manual"),
        ("6 day", "6 day"),
        ("6 week", "6 week"),
        ("6 month", "6 month"),
        # for told messages without link to previous trace
        ("unrecognized_patient", "unrecognized_patient")
    )

    INITIATOR_CHOICES = (
        ("admin", "admin"),
        ("clinic_worker", "clinic_worker"),
        ("automated_task", "automated_task"),
        ("cba", "cba"),
    )

    initiator = models.CharField(choices=INITIATOR_CHOICES, max_length=20)

    # person who initiates the tracing (used when initiator=clinic_worker)
    initiator_contact = models.ForeignKey(
        Contact, related_name='patients_traced',
        limit_choices_to={'types__slug': 'clinic_worker'},
        null=True, blank=True)

    clinic = models.ForeignKey(Location, related_name='patient_location',
                               null=True, blank=True)

    type = models.CharField(choices=TYPE_CHOICES, max_length=30)
    # name of patient to trace
    name = models.CharField(max_length=50)

    #  why the trace was initiated
    # reason = models.CharField(max_length=90)

    patient_event = models.ForeignKey(PatientEvent,
                                      related_name='patient_traces',
                                      null=True, blank=True)
    # cba who informs patient
    messenger = models.ForeignKey(
        Contact, related_name='patients_reminded',
        limit_choices_to={'types__slug': 'cba'}, null=True, blank=True)

    # cba who confirms that patient visited clinic
    confirmed_by = models.ForeignKey(
        Contact, related_name='patient_traces_confirmed',
        limit_choices_to={'types__slug': 'cba'}, null=True,
        blank=True)

    # status of tracing activity
    status = models.CharField(choices=STATUS_CHOICES, max_length=25)

    # date when tracing starts
    start_date = models.DateTimeField()
    # date when cba tells mother
    reminded_date = models.DateTimeField(null=True, blank=True)
    # date of confirmation that patient visited clinic
    confirmed_date = models.DateTimeField(null=True, blank=True)

    def save(self, * args, ** kwargs):
        if not self.pk:
            self.start_date = datetime.datetime.now()
        super(PatientTrace, self).save(*args, ** kwargs)


def get_status_new():
    return PatientTrace.STATUS_CHOICES[0][1]


def get_status_told():
    return PatientTrace.STATUS_CHOICES[1][1]


def get_status_await_confirm():
    return PatientTrace.STATUS_CHOICES[3][1]


def get_status_confirmed():
    return PatientTrace.STATUS_CHOICES[2][1]


def get_status_found():
    return PatientTrace.STATUS_CHOICES[4][1]


def get_status_refused():
    return PatientTrace.STATUS_CHOICES[5][1]


def get_status_lost():
    return PatientTrace.STATUS_CHOICES[6][1]


def get_status_transfered():
    return PatientTrace.STATUS_CHOICES[7][1]


def get_status_deceased():
    return PatientTrace.STATUS_CHOICES[8][1]


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
