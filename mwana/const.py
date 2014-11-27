# vim: ai ts=4 sts=4 et sw=4
from django.conf import settings

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.locations.models import LocationType

# contact types:
LAB_WORKER_SLUG = settings.RESULTS160_SLUGS.get('LAB_WORKER_SLUG', 'hub')
HUB_WORKER_SLUG = settings.RESULTS160_SLUGS.get('HUB_WORKER_SLUG', 'hub')
CBA_SLUG = settings.RESULTS160_SLUGS.get('CBA_SLUG', 'cba')
PATIENT_SLUG = settings.RESULTS160_SLUGS.get('PATIENT_SLUG', 'patient')
CLINIC_WORKER_SLUG = settings.RESULTS160_SLUGS.get('CLINIC_WORKER_SLUG',
                                                   'clinic-worker')
DISTRICT_WORKER_SLUG = settings.RESULTS160_SLUGS.get('DISTRICT_WORKER_SLUG',
                                                     'district-worker')
PROVINCE_WORKER_SLUG = settings.RESULTS160_SLUGS.get('PROVINCE_WORKER_SLUG',
                                                     'province-worker')
DBS_PRINTER_SLUG = settings.RESULTS160_SLUGS.get('DBS_PRINTER_SLUG',
                                                 'dbs-printer')
CHILD_SLUG = settings.RESULTS160_SLUGS.get('CHILD_SLUG', 'child-patient')
MOTHER_SLUG = settings.RESULTS160_SLUGS.get('MOTHER_SLUG', 'mother-patient')
VOLUNTEER_SLUG = settings.RESULTS160_SLUGS.get('VOLUNTEER_SLUG', 'volunteer')

# location types:
CLINIC_SLUGS = settings.RESULTS160_SLUGS.get('CLINIC_SLUGS', ('clinic',))
ZONE_SLUGS = settings.RESULTS160_SLUGS.get('ZONE_SLUGS', ('zone',))
DISTRICT_SLUGS = settings.RESULTS160_SLUGS.get('DISTRICT_SLUGS', ('district',))

# PROVINCE_SLUGS is optional (not all countries have provinces)
# it should NOT be set to None, as that would cause filters by the 'province'
# type to effectively return any type of location
PROVINCE_SLUGS = settings.RESULTS160_SLUGS.get('PROVINCE_SLUGS', ('province',))

# apps
LAB_RESULTS_APP = "mwana.apps.labresults"


def _get_contacttype(slug, name):
    try:
        type = ContactType.objects.get(slug__iexact=slug)
    except ContactType.DoesNotExist:
        type = ContactType.objects.create(name=name, slug=slug)
    return type


def _get_locationtype(slug, singular, plural=None):
    if not plural:
        plural = singular + 's'
    try:
        type = LocationType.objects.get(slug__iexact=slug)
    except LocationType.DoesNotExist:
        type = LocationType.objects.create(singular=singular, slug=slug,
                                           plural=plural)
    return type


def get_lab_worker_type():
    return _get_contacttype(LAB_WORKER_SLUG, 'LAB Worker')


def get_hub_worker_type():
    return _get_contacttype(HUB_WORKER_SLUG, 'Hub Worker')


def get_cba_type():
    return _get_contacttype(CBA_SLUG, 'Community Based Agent')


def get_dbs_printer_type():
    return _get_contacttype(DBS_PRINTER_SLUG, 'DBS Printer')


def get_patient_type():
    return _get_contacttype(PATIENT_SLUG, 'Patient')


def get_child_type():
    return _get_contacttype(CHILD_SLUG, 'Child')


def get_mother_type():
    return _get_contacttype(MOTHER_SLUG, 'Mother')


def get_zone_type():
    return _get_locationtype(ZONE_SLUGS, 'Zone')


def get_clinic_worker_type():
    return _get_contacttype(CLINIC_WORKER_SLUG, 'Clinic Worker')


def get_district_worker_type():
    return _get_contacttype(DISTRICT_WORKER_SLUG, 'District Worker')


def get_province_worker_type():
    return _get_contacttype(PROVINCE_WORKER_SLUG, 'Province Worker')


def get_nutrition_worker_type():
    return _get_contacttype(NUTRITION_WORKER_SLUG, 'Nutrition Interviewer')


def get_nutrition_patient_type():
    return _get_contacttype(NUTRITION_PATIENT_SLUG, 'Nutrition Patient')


def get_volunteer_type():
    return _get_contacttype(VOLUNTEER_SLUG, 'Volunteer')
