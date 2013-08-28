# vim: ai ts=4 sts=4 et sw=4
""" This script corrects/updates PatientTrace records that were auto-initiated by
the system but were not subsequently updated due to a bug that has since been
fixed
"""
from datetime import timedelta
import re

from django.core.management.base import LabelCommand
from django.db.models import Q
from mwana.apps.patienttracing.models import CorrectedTrace
from mwana.apps.patienttracing.models import PatientTrace
from mwana.apps.reminders.models import PatientEvent
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

def clean_names():
    count = 0
    # clean patient event's name
    for pe in PatientEvent.objects.filter(patient__name__iregex='\d\d .*'):
        patient = pe.patient
        name = re.sub(r"\d\d", "", patient.name).lower().strip()
        name = re.sub(r"\s+", " ", name)

        if name.startswith("f "):
            pe.event_location_type = 'cl'
            pe.save()
            name = name[2:]
        elif name.startswith("h "):
            pe.event_location_type = 'hm'
            pe.save()
            name = name[2:]

        name = name.strip().title()
        patient.name = name
        patient.save()
        count += 1

    # clean name in patient trace
    for pt in PatientTrace.objects.filter(name__iregex='\d\d .*'):
        name = re.sub(r"\d\d", "", pt.name).lower().strip().title()
        name = re.sub(r"\s+", " ", name)
        pt.name = name
        pt.save()

    for pt in PatientTrace.objects.filter(name__istartswith='f '):
        pt.name = pt.name[2:].strip().title()
        pt.save()
        count += 1

    for pt in PatientTrace.objects.filter(name__istartswith='h '):
        pt.name = pt.name[2:].strip().title()
        pt.save()
        count += 1

    for pt in PatientTrace.objects.filter(name__istartswith='mwana '):
        pt.name = pt.name[6:].strip().title()
        pt.save()
        count += 1

    for pt in PatientTrace.objects.filter(Q(name__contains='6'),
                                          Q(name__icontains='day') |
                                          Q(name__icontains='week') |
                                          Q(name__icontains='month')):
        name = pt.name.strip().lower()
        for item in ['6days', '6 days', '6weeks', '6 weeks', '6months', '6 months',
            "6day", "6 day", "6week", "6 week", "6month", "6 month"]:
            name = name.replace(item, "")

        pt.name = name.strip().title()
        pt.save()
        count += 1

    print "Made %s corrections to names" % count

def correct_patient_traces():
    clean_names()
    correct_missing_clinic()
    correct_misspelt_status()
    correct_tolds()
    correct_confirms()
    cleanup()