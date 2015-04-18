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

# These correspond to the sample id suffixes in the labresults.result
LAB_NAME = {'1': "KCH DNA-PCR LAB", '2': "QECH DNA-PCR LAB",
            '3': "MCH DNA-PCR LAB", '4': "MDH DNA-PCR LAB",
            '5': "PIH DNA-PCR LAB", '6': "DREAM-BT DNA-PCR LAB",
            '8': "Zomba DNA-PCR LAB", '9': "TESTING DNA-PCR LAB"}

COUNTRY_CODE = '+265'

DATE_FORMAT = 'F j, Y'  # December 25, 2012
DATE_INPUT_FORMATS = ('%d%m%Y', '%Y-%m-%d')

DISTRICTS = sorted(["Dedza", "Dowa", "Kasungu", "Lilongwe", "Mchinji",
                    "Nkhotakota", "Ntcheu", "Ntchisi", "Salima", "Chitipa",
                    "Karonga", "Likoma", "Mzimba", "Nkhata Bay", "Rumphi",
                    "Balaka", "Blantyre", "Chikwawa", "Chiradzulu", "Machinga",
                    "Mangochi", "Mulanje", "Mwanza", "Nsanje", "Thyolo",
                    "Phalombe", "Zomba", "Neno"])

TIME_ZONE = 'Africa/Blantyre'

LANGUAGE_CODE = 'eng-us'

LOCATION_CODE_CLASS = 'mwana.malawi.locations.LocationCode'

MALAWI_ROOT = os.path.abspath(os.path.dirname(__file__))
STATICFILES_DIRS += (os.path.join(MALAWI_ROOT, "static"),)
TEMPLATE_DIRS += (os.path.join(MALAWI_ROOT, "templates"),)
ROOT_URLCONF = 'mwana.malawi.urls'

# INSTALLED APPS
INSTALLED_APPS.append("mwana.apps.reports.webreports")
# INSTALLED_APPS.insert(-1, 'eav')
# INSTALLED_APPS.insert(-1, 'uni_form')
# INSTALLED_APPS.insert(-1, 'rapidsms_xforms')
INSTALLED_APPS.insert(-1, 'people')
INSTALLED_APPS.insert(-1, 'django_filters')
INSTALLED_APPS.insert(-1, 'mwana.apps.nutrition')
INSTALLED_APPS.insert(-1, 'mwana.apps.training')
INSTALLED_APPS.insert(-1, 'mwana.apps.appointments')
INSTALLED_APPS.insert(-1, 'django_tables2_reports')
INSTALLED_APPS.insert(-1, 'mwana.apps.remindmi')
INSTALLED_APPS.insert(-1, 'mwana.apps.dhis2')
INSTALLED_APPS.insert(-1, 'mwana.apps.monitor')
INSTALLED_APPS.insert(-1, 'mwana.apps.emergency')

# Add the people and growth monitoring apps for Malawi:
# don't append, 'default' app should come last:

DEFAULT_RESPONSE = '''Invalid Keyword. Use GM for Growth Monitor, MWANA or MAYI
 for RemindMi, CHECK or RESULT for Results160 and FLOOD for
 emergency. Send HELP for more information'''

# we need separate migration modules for the rapidsms app in Malawi and
# Zambia, because different 3rd party apps add different model extensions
SOUTH_MIGRATION_MODULES = {
    'rapidsms': 'mwana.malawi.migrations.rapidsms',
    'locations': 'mwana.malawi.migrations.locations',
    'reminders': 'mwana.malawi.migrations.reminders',
}

# reduce noise in logs
LOG_LEVEL = "INFO"
#XFORMS_HOST = '127.0.0.1:8000'

# paginator configuration
PAGINATOR_OBJECTS_PER_PAGE = 50

# MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES.extend(
#     ['django_tables2_reports.middleware.TableReportMiddleware', ])

# XLS exports
EXCEL_SUPPORT = 'xlwt'

# Celery config

CELERY_TIMEZONE = 'Africa/Blantyre'

# WSGI_APPLICATION = "mwana.malawi.apache.wsgi.application"

RAPIDSMS_HANDLERS = [
    "mwana.apps.emergency.handlers.flood.FloodHandler",
    "mwana.apps.help.handlers.help.HelpHandler",
    "mwana.apps.help.handlers.facilitycode.CodeHandler",
    "mwana.apps.help.handlers.facilitycontacts.ContactsHandler",
    "mwana.apps.labresults.handlers.join.JoinHandler",
    "mwana.apps.labresults.handlers.leave.UnregisterHandler",
    "mwana.apps.labresults.handlers.printer.PrinterHandler",
    "mwana.apps.labresults.handlers.results.ResultsHandler",
    "mwana.apps.labresults.handlers.sent.SentHandler",
    "mwana.apps.labresults.handlers.eid.EIDHandler",
    "mwana.apps.labresults.handlers.request.RequestCallHandler",
    # "mwana.apps.broadcast.handlers.all.AllHandler",
    "mwana.apps.broadcast.handlers.blaster.BlastHandler",
    "mwana.apps.broadcast.handlers.cba.CBAHandler",
    "mwana.apps.broadcast.handlers.clinic.ClinicHandler",
    "mwana.apps.broadcast.handlers.district.DistrictHandler",
    "mwana.apps.broadcast.handlers.hsa.HSAHandler",
    "mwana.apps.broadcast.handlers.msg.MessageHandler",
    "mwana.apps.nutrition.handlers.growth.GrowthHandler",
    "mwana.apps.nutrition.handlers.cancel.CancelHandler",
    # "mwana.apps.remindmi.handlers.mayi.MayiHandler",
    "mwana.apps.remindmi.handlers.mwana.MwanaHandler",
    "mwana.apps.remindmi.handlers.status.StatusHandler",
    "mwana.apps.remindmi.handlers.discontinue.DiscontinueHandler",
    "mwana.apps.remindmi.handlers.collect.CollectHandler",
    "mwana.apps.remindmi.handlers.refill.RefillHandler",
    "mwana.apps.patienttracing.handlers.trace.TraceHandler",
    "mwana.apps.training.handlers.training.TrainingHandler",
    # "mwana.apps.reminders.handlers.mwana.MwanaHandler",
    # "mwana.apps.reminders.handlers.mayi.MayiHandler",
    # "mwana.apps.reminders.handlers.discontinue.DiscontinueHandler",
    # "mwana.apps.patienttracing.handlers.confirm.ConfirmHandler",
    # "mwana.apps.patienttracing.handlers.told.ToldHandler",
    # "mwana.apps.training.handlers.trainingstop.TrainingStopHandler",
    # "mwana.apps.training.handlers.trainingstop.TrainingStopHandler",
]
