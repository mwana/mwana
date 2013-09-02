# vim: ai ts=4 sts=4 et sw=4
""" This script corrects/updates PatientTrace records that were auto-initiated by
the system but were not subsequently updated due to a bug that has since been
fixed. Also corrects patient traces arising from user errors when typing names.
"""
from datetime import timedelta
import re
import string

from django.core.management.base import LabelCommand
from django.db.models import Q
from mwana.apps.patienttracing.models import CorrectedTrace
from mwana.apps.patienttracing.models import PatientTrace
from mwana.apps.reminders.models import PatientEvent
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from mwana.util import get_clinic_or_default
from rapidsms.models import Contact

class Command(LabelCommand):
    help = """Corrects PatientTrace objects that were system initiated"""
   
    
    def handle(self, * args, ** options):
        told_window = None
        confirm_window = None
        if args:
            if args[0].isdigit():
                told_window = int(args[0])
            if len(args) > 1 and args[1].isdigit():
                confirm_window = int(args[1])

        correct_patient_traces(told_window, confirm_window)
       
       
def correct_missing_clinic():
    for pe in PatientEvent.objects.filter(patient__location=None).\
    exclude(cba_conn__contact__location=None):
        patient = pe.patient
        patient.location = pe.cba_conn.contact.location
        patient.save()
        
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


def correct_tolds(days_ago):
    if not days_ago: days_ago = 7
    count = 0
    for pt in PatientTrace.objects.filter(source_patient_trace=None,
                                          initiator='cba', status='told',
                                          patient_event=None):
        messenger = pt.messenger
        reminded_date = pt.reminded_date
        date_ago = reminded_date - timedelta(days=days_ago)
        name = pt.name
        clinic = get_clinic_or_default(messenger)

        # find exact match
        for auto_pt in PatientTrace.objects.filter(initiator__in=["automated_task"],
                                                   status='new',
                                                   start_date__gte=date_ago,
                                                   start_date__lte=reminded_date,
                                                   patient_event__patient__name__iexact=name,
                                                   patient_event__patient__location__parent=clinic).order_by("-start_date"):
            auto_pt.messenger = messenger
            auto_pt.reminded_date = reminded_date
            auto_pt.status = pt.status
            auto_pt.save()
            CorrectedTrace.objects.get_or_create(copied_from=pt, copied_to=auto_pt)
            count += 1
        
        # else try matching by soundex and distance method
        else:
            for my_pt in PatientTrace.objects.filter(initiator__in=["automated_task"],
                                                   status='new',
                                                   start_date__gte=date_ago,
                                                   start_date__lte=reminded_date,
                                                   patient_event__patient__location__parent=clinic).order_by("-start_date"):
                if _names_tally(name, my_pt.name):
                    my_pt.messenger = messenger
                    my_pt.reminded_date = reminded_date
                    my_pt.status = pt.status
                    my_pt.save()
                    CorrectedTrace.objects.get_or_create(copied_from=pt, copied_to=my_pt)
                    count += 1                    

        for my_pt in PatientTrace.objects.filter(initiator__in=["clinic_worker"],
                                                 status='new',
                                                 start_date__gte=date_ago,
                                                 start_date__lte=reminded_date,
                                                 name__iexact=name.strip(),
                                                 clinic=clinic).order_by("-start_date"):
            my_pt.messenger = messenger
            my_pt.reminded_date = reminded_date
            my_pt.status = pt.status
            my_pt.save()
            CorrectedTrace.objects.get_or_create(copied_from=pt, copied_to=my_pt)
            count += 1
        
        # else try matching by soundex and distance method
        else:
            for my_pt in PatientTrace.objects.filter(initiator__in=["clinic_worker"],
                                                 status='new',
                                                 start_date__gte=date_ago,
                                                 start_date__lte=reminded_date,
                                                 clinic=clinic).order_by("-start_date"):
                if _names_tally(name, my_pt.name):
                    my_pt.messenger = messenger
                    my_pt.reminded_date = reminded_date
                    my_pt.status = pt.status
                    my_pt.save()
                    CorrectedTrace.objects.get_or_create(copied_from=pt, copied_to=my_pt)
                    count += 1
                    

    print "corrected %s records with told using %s days as tolerance" % (count, days_ago)


def correct_confirms(days_ago=7):
    if not days_ago: days_ago = 7
    count = 0
    for pt in PatientTrace.objects.filter(source_patient_trace=None,
                                          initiator='cba', status='confirmed',
                                          patient_event=None).exclude(reminded_date=None):
        messenger = pt.messenger
        reminded_date = pt.reminded_date
        date_ago = reminded_date - timedelta(days=days_ago)
        confirmed_date = pt.confirmed_date
        name = pt.name
        clinic = get_clinic_or_default(messenger)

        for auto_pt in PatientTrace.objects.filter(initiator="automated_task",
                                                   status__in=['new', 'told'],
                                                   start_date__gte=date_ago,
                                                   start_date__lte=reminded_date,
                                                   patient_event__patient__name__iexact=name,
                                                   patient_event__patient__location__parent=clinic).order_by("-start_date"):
            auto_pt.messenger = messenger
            if not auto_pt.reminded_date:
                auto_pt.reminded_date = reminded_date
            auto_pt.confirmed_date = confirmed_date
            auto_pt.status = pt.status
            auto_pt.confirmed_by = pt.confirmed_by or pt.messenger
            auto_pt.save()

            CorrectedTrace.objects.get_or_create(copied_from=pt, copied_to=auto_pt)

            count += 1

        # else try matching by soundex and distance method
        else:
            for my_pt in PatientTrace.objects.filter(initiator="automated_task",
                                                   status__in=['new', 'told'],
                                                   start_date__gte=date_ago,
                                                   start_date__lte=reminded_date,
                                                   patient_event__patient__location__parent=clinic).order_by("-start_date"):
                if _names_tally(name, my_pt.name):
                    my_pt.messenger = messenger
                    if not my_pt.reminded_date:
                        my_pt.reminded_date = reminded_date
                    my_pt.confirmed_date = confirmed_date
                    my_pt.status = pt.status
                    my_pt.confirmed_by = pt.confirmed_by or pt.messenger
                    my_pt.save()
                    CorrectedTrace.objects.get_or_create(copied_from=pt, copied_to=my_pt)
                    count += 1
                    

        for my_pt in PatientTrace.objects.filter(initiator="clinic_worker",
                                                 status__in=['new', 'told'],
                                                 start_date__gte=date_ago,
                                                 start_date__lte=reminded_date,
                                                 name__iexact=name,
                                                 clinic=clinic).order_by("-start_date"):
            my_pt.messenger = messenger
            if not my_pt.reminded_date:
                my_pt.reminded_date = reminded_date
            my_pt.confirmed_date = confirmed_date
            my_pt.status = pt.status
            my_pt.confirmed_by = pt.confirmed_by or pt.messenger
            my_pt.save()

            CorrectedTrace.objects.get_or_create(copied_from=pt, copied_to=my_pt)

            count += 1

        # else try matching by soundex and distance method
        else:
            for my_pt in PatientTrace.objects.filter(initiator="clinic_worker",
                                                 status__in=['new', 'told'],
                                                 start_date__gte=date_ago,
                                                 start_date__lte=reminded_date,
                                                 clinic=clinic).order_by("-start_date"):
                if _names_tally(name, my_pt.name):
                    my_pt.messenger = messenger
                    if not my_pt.reminded_date:
                        my_pt.reminded_date = reminded_date
                    my_pt.confirmed_date = confirmed_date
                    my_pt.status = pt.status
                    my_pt.confirmed_by = pt.confirmed_by or pt.messenger
                    my_pt.save()
                    
                    CorrectedTrace.objects.get_or_create(copied_from=pt, copied_to=my_pt)
                    count += 1
                    

    print "corrected %s records with confirm using %s days as tolerance" % (count, days_ago)

def cleanup():
    # TODO: clear CBA initiated traces that have been mapped to system initiated ones
    pass


def _clean(name):
    return name.translate(string.maketrans("", ""), string.punctuation).strip().title()

def _names_tally(first, second):
    name1, name2 = first.strip().lower(), second.strip().lower()
    if name1 == name2:
        return True

    cleaner = InputCleaner()

    if cleaner.ldistance(name1, name2) <= 2:
        return True
    try:
        if cleaner.ldistance(name1, name2) <= 4 and \
            cleaner.soundex(name1) == cleaner.soundex(name2):
            return True
    except UnicodeEncodeError:
        return False
    # check for e.g. Trevor M Sinkala against Sinkala Trevor, Sara Daka vs Sarah Daka
    if len(name1) > 8 and len(name2) > 8 and " " in name1 and " " in name2:
        if all(item in name1 for item in name2.split()):            
            return True
        if all(item in name2 for item in name1.split()):            
            return True

    return False


def _remove_punctuation(count):
    for token in string.punctuation:
        pts = PatientTrace.objects.filter(name__contains=token)
        for pt in pts:
            pt.name = pt.name.replace(token, "").strip().title()
            pt.save()
            count += 1

        contacts = Contact.objects.filter(name__contains=token)
        for contact in contacts:
            contact.name = contact.name.replace(token, "").strip().title()
            contact.save()
            count = + 1
    return count


def _remove_leading_space(count):
    for pt in PatientTrace.objects.filter(name__startswith=" "):
        pt.name = pt.name.strip().title()
        pt.save()
        count += 1

    for contact in Contact.objects.filter(name__startswith=" "):
        contact.name = contact.name.strip().title()
        contact.save()
        count = + 1

    return count


def _remove_extra_spaces(count):
    for pt in PatientTrace.objects.filter(name__contains="  "):
        pt.name = re.sub(r"\s+", " ", pt.name).strip().title()
        pt.save()
        count += 1
    return count


def _remove_date_numbers(count):
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
    for pt in PatientTrace.objects.filter(name__iregex='\d\d .*'):
        name = re.sub(r"\d\d", "", pt.name).lower().strip().title()
        name = re.sub(r"\s+", " ", name)
        pt.name = name
        pt.save()
        count += 1
    return count


def _remove_locationtype_specifier(count):
    for pt in PatientTrace.objects.filter(name__istartswith='f '):
        pt.name = pt.name[2:].strip().title()
        pt.save()
        count += 1
    for pt in PatientTrace.objects.filter(name__istartswith='h '):
        pt.name = pt.name[2:].strip().title()
        pt.save()
        count += 1
    return count


def _remove_clinic_data(count):
    for pt in PatientTrace.objects.filter(name__icontains='clinic',
                                          initiator__in=['cba', 'clinic_worker']):
        pt.name = " ".join(pt.name.split()[:2]).title()
        pt.save()
        count += 1
    return count


def _remove_visit_type(count):
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
    return count


def _remove_extraneous_words(count):
    for pt in PatientTrace.objects.filter(name__istartswith='mwana '):
        pt.name = pt.name[6:].strip().title()
        pt.save()
        count += 1
    return count


def clean_names():
    count = 0
    count = _remove_punctuation(count)

    count = _remove_leading_space(count)

    count = _remove_extra_spaces(count)

    count = _remove_date_numbers(count)

    count = _remove_locationtype_specifier(count)

    count = _remove_extraneous_words(count)

    count = _remove_clinic_data(count)

    count = _remove_visit_type(count)

    print "Made %s corrections to names" % count

def correct_patient_traces(told_tolerance=None, confirm_tolerance=None):
    clean_names()
    correct_missing_clinic()
    correct_misspelt_status()
    correct_tolds(told_tolerance)
    correct_confirms(confirm_tolerance)
    cleanup()
