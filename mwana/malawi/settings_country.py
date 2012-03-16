# vim: ai ts=4 sts=4 et sw=4
import os.path
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

GROWTHMONITORING_SETTINGS = {'DEFAULT_LANG': 'en'}

# The TLC printers require 2 chars at the beginning of the message, so reduce
# the size of all outgoing messages by 2 chars here
MAX_SMS_LENGTH = 158

ADH_LAB_NAME = "QECH DNA-PCR LAB"

COUNTRY_CODE = '+265'

TIME_ZONE = 'Africa/Blantyre'

LANGUAGE_CODE = 'eng-us'

LOCATION_CODE_CLASS = 'mwana.malawi.locations.LocationCode'

MALAWI_ROOT = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIRS = (os.path.join(MALAWI_ROOT, "templates"),)
MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + ['pagination.middleware.PaginationMiddleware',]
ROOT_URLCONF = 'mwana.malawi.urls'

# Add XForms app + navigation and webreports:
INSTALLED_APPS.append("mwana.apps.reports.webreports")
INSTALLED_APPS.insert(-1, 'eav')
INSTALLED_APPS.insert(-1, 'uni_form')
INSTALLED_APPS.insert(-1, 'pagination')
INSTALLED_APPS.insert(-1, 'rapidsms_xforms')
RAPIDSMS_TABS.append(('mwana_reports', 'Reports'))
#RAPIDSMS_TABS.append(('xforms', 'XForms'))

# Add the people and growth monitoring apps for Malawi:
# don't append, 'default' app should come last:
INSTALLED_APPS.insert(-1, 'people')
INSTALLED_APPS.insert(-1, 'mwana.apps.nutrition')
RAPIDSMS_TABS.append(('growth_index', 'Growth Monitor'))
RAPIDSMS_TABS.append(('growth_graphs', 'Nutrition Reports'))

DEFAULT_RESPONSE = "Invalid Keyword. Keywords are GM for Growth Monitor, MWANA for RemindMi, ALL for Broadcast and CHECK or RESULT for Results160. Send HELP for more information"

# we need separate migration modules for the rapidsms app in Malawi and
# Zambia, because different 3rd party apps add different model extensions
SOUTH_MIGRATION_MODULES = {
    'rapidsms': 'mwana.malawi.migrations.rapidsms',
    'locations': 'mwana.malawi.migrations.locations',
}

# reduce noise in logs
LOG_LEVEL = "INFO"
