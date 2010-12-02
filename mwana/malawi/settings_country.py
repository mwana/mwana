# vim: ai ts=4 sts=4 et sw=4
from mwana.settings_project import *

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
RESULTS160_SCHEDULES = {
    # send new results at 8:00am M-F
    'send_results_notification': {'hours': [8], 'minutes': [0],
                                  'days_of_week': [0, 1, 2, 3, 4]},
    # send changed results at 7:30am M-F
    'send_changed_records_notification': {'hours': [7], 'minutes': [30],
                                          'days_of_week': [0, 1, 2, 3, 4]},
}
RESULTS160_FAKE_ID_FORMAT = '{clinic}-{id:04d}-1'
RESULTS160_RESULT_DISPLAY = {'N': 'Negative', 'P': 'Positive'}

# The TLC printers require 2 chars at the beginning of the message, so reduce
# the size of all outgoing messages by 2 chars here
MAX_SMS_LENGTH = 158

COUNTRY_CODE = '+265'

TIME_ZONE = 'Africa/Blantyre'

LANGUAGE_CODE = 'eng-us'

LOCATION_CODE_CLASS = 'mwana.malawi.locations.LocationCode'

ROOT_URLCONF = 'mwana.malawi.urls'

# Add XForms app + navigation:
INSTALLED_APPS.insert(-1, 'eav')
INSTALLED_APPS.insert(-1, 'uni_form')
INSTALLED_APPS.insert(-1, 'rapidsms_xforms')
RAPIDSMS_TABS.append(('xforms', 'XForms'))
