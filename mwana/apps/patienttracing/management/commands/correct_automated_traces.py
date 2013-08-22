# vim: ai ts=4 sts=4 et sw=4
""" This script corrects/updates PatientTrace records that were auto-initiated by
the system but were not subsequently updated due to a bug that has since been
fixed
"""
from datetime import timedelta

from django.core.management.base import LabelCommand
from mwana.apps.patienttracing.models import CorrectedTrace
from mwana.apps.patienttracing.models import PatientTrace
from mwana.util import get_clinic_or_default


class Command(LabelCommand):
    help = """Corrects PatientTrace objects that were system initiated"""
   
    
    def handle(self, * args, ** options):
        correct_patient_traces()
       
       
def correct_missing_clinic():
    for pt in PatientTrace.objects.filter(clinic=None, initiator='automated_task'):
        pt.clinic = get_clinic_or_default(pt.patient_event.patient)
        pt.save()


def correct_misspelt_status():
    for pt in PatientTrace.objects.filter(status='Told'):
        pt.status = 'told'
        pt.save()

    for pt in PatientTrace.objects.filter(status='Confirmed'):
        pt.status = 'confirmed'
        pt.save()


def correct_tolds():
    pt = PatientTrace()
    count = 0
    for pt in PatientTrace.objects.filter(initiator='cba', status='told', patient_event=None):
        messenger = pt.messenger
        reminded_date = pt.reminded_date
        date_ago = reminded_date - timedelta(days=3)
        name = pt.name
        clinic = get_clinic_or_default(messenger)

        for auto_pt in PatientTrace.objects.filter(initiator="automated_task",
                                                   status='new',
                                                   start_date__gte=date_ago,
                                                   start_date__lte=reminded_date,
                                                   patient_event__patient__name__iexact=name,
                                                   patient_event__patient__location__parent=clinic):
            auto_pt.messenger = messenger
            auto_pt.reminded_date = reminded_date
            auto_pt.status = pt.status
            auto_pt.save()
            CorrectedTrace.objects.get_or_create(copied_from=pt, copied_to=auto_pt)
            count += 1

    print "corrected %s records with told" % count


def correct_confirms():
    pt = PatientTrace()
    count = 0
    for pt in PatientTrace.objects.filter(initiator='cba', status='confirmed',
                                          patient_event=None).exclude(reminded_date=None):
        messenger = pt.messenger
        reminded_date = pt.reminded_date
        date_ago = reminded_date - timedelta(days=3)
        confirmed_date = pt.confirmed_date
        name = pt.name
        clinic = get_clinic_or_default(messenger)

        for auto_pt in PatientTrace.objects.filter(initiator="automated_task",
                                                   status__in=['new', 'told'],
                                                   start_date__gte=date_ago,
                                                   start_date__lte=reminded_date,
                                                   patient_event__patient__name__iexact=name,
                                                   patient_event__patient__location__parent=clinic):
            auto_pt.messenger = messenger
            if not auto_pt.reminded_date:
                auto_pt.reminded_date = reminded_date
            auto_pt.confirmed_date = confirmed_date
            auto_pt.status = pt.status
            auto_pt.confirmed_by = pt.confirmed_by or pt.messenger
            auto_pt.save()

            CorrectedTrace.objects.get_or_create(copied_from=pt, copied_to=auto_pt)

            count += 1

    print "corrected %s records with confirm" % count

def cleanup():
    # TODO: clear CBA initiated traces that have been mapped to system initiated ones
    pass

def correct_patient_traces():
    correct_missing_clinic()
    correct_misspelt_status()
    correct_tolds()
    correct_confirms()
    cleanup()