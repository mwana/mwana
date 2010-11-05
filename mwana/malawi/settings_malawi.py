from mwana.settings_project import *

# Zambia:
#RESULTS160_SLUGS = {
#    'CBA_SLUG' = 'cba',
#    'PATIENT_SLUG': 'patient',
#    'CLINIC_WORKER_SLUG': 'worker',
#    # location types:
#    'CLINIC_SLUGS': ('urban_health_centre', '1st_level_hospital',
#                    'rural_health_centre', 'health_post'),
#    'ZONE_SLUGS': ('zone',),
#    'DISTRICT_SLUGS': ('districts',), # XXX verify me
#    'PROVINCE_SLUGS': ('provinces',), # XXX verify me
#}

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
