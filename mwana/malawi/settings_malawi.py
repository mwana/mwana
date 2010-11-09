from mwana.settings_project import *

# Add the people and growth monitoring apps for Malawi:
# don't append, 'default' app should come last:
INSTALLED_APPS.insert(-1, 'people')
INSTALLED_APPS.insert(-1, 'growthmonitoring')

RAPIDSMS_TABS.append(('growth_index', 'Growth Monitoring'))

# Malawi:
RESULTS160_SLUGS = {
    'CBA_SLUG': 'cba',
    'PATIENT_SLUG': 'patient',
    'CLINIC_WORKER_SLUG': 'clinic-worker',
    'DISTRICT_WORKER_SLUG': 'district-worker',
    # location types:
    'CLINIC_SLUGS': ('clinic', 'health_centre', 'hospital', 'maternity',
                     'dispensary', 'rural_hospital', 'mental_hospital',
                     'district_hospital', 'central_hospital',
                     'voluntary_counselling', 'rehabilitation_centre'),
    'ZONE_SLUGS': ('zone',),
    'DISTRICT_SLUGS': ('district',),
}

TIME_ZONE = 'Africa/Blantyre'

LANGUAGE_CODE = 'eng-us'

LOCATION_CODE_CLASS = 'mwana.malawi.locations.LocationCode'

ROOT_URLCONF = 'mwana.malawi.urls'

GROWTHMONITORING_SETTINGS = {'DEFAULT_LANG': 'en'}
