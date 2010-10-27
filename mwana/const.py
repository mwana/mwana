from mwana.apps.contactsplus.models import ContactType
from rapidsms.contrib.locations.models import LocationType

# contact types:
CBA_SLUG = 'cba'
PATIENT_SLUG = 'patient'
CLINIC_WORKER_SLUG = 'worker'

# location types:
CLINIC_SLUGS = ('urban_health_centre', '1st_level_hospital',
                'rural_health_centre', 'health_post')
ZONE_SLUG = 'zone'

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


def get_cba_type():
    return _get_contacttype(CBA_SLUG, 'Community Based Agent')


def get_patient_type():
    return _get_contacttype(PATIENT_SLUG, 'Patient')


def get_clinic_worker_type():
    return _get_contacttype(CLINIC_WORKER_SLUG, 'Clinic Worker')


def get_zone_type():
    return _get_locationtype(ZONE_SLUG, 'Zone')
