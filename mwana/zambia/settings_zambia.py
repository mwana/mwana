from mwana.settings_project import *

# Zambia:
RESULTS160_SLUGS = {
    'CBA_SLUG': 'cba',
    'PATIENT_SLUG': 'patient',
    'CLINIC_WORKER_SLUG': 'worker',
    # location types:
    'CLINIC_SLUGS': ('urban_health_centre', '1st_level_hospital',
                    'rural_health_centre', 'health_post'),
    'ZONE_SLUGS': ('zone',),
    'DISTRICT_SLUGS': ('districts',), # XXX verify me
    'PROVINCE_SLUGS': ('provinces',), # XXX verify me
}

TIME_ZONE = 'Africa/Lusaka'

LANGUAGE_CODE = 'bem-zm'

LOCATION_CODE_CLASS = 'mwana.zambia.locations.LocationCode'
