# vim: ai ts=4 sts=4 et sw=4
from mwana.settings_project import *

_ = lambda s:s

# Zambia:
RESULTS160_SLUGS = {
    'CBA_SLUG': 'cba',
    'PATIENT_SLUG': 'patient',
    'CLINIC_WORKER_SLUG': 'worker',
    'DISTRICT_WORKER_SLUG': 'district',
    'PROVINCE_WORKER_SLUG': 'province',
    'HUB_WORKER_SLUG': 'hub',
    'LAB_WORKER_SLUG': 'lab',
    # location types:
    'CLINIC_SLUGS': ('urban_health_centre', '1st_level_hospital','2nd_level_hospital',
                     'rural_health_centre', 'health_post', 'clinic', 'hahc'),
    'ZONE_SLUGS': ('zone', ),
    'DISTRICT_SLUGS': ('districts', ), # XXX verify me
    'PROVINCE_SLUGS': ('provinces', ), # XXX verify me
}
INSTALLED_APPS.append("mwana.apps.reports.webreports")
INSTALLED_APPS.append("mwana.apps.userverification")
INSTALLED_APPS.append("mwana.apps.filteredlogs")
INSTALLED_APPS.append("mwana.apps.monitor")
INSTALLED_APPS.append("mwana.apps.websmssender")
INSTALLED_APPS.append("mwana.apps.issuetracking")
INSTALLED_APPS.append("mwana.apps.email")
INSTALLED_APPS.append("mwana.apps.birthcertification")
INSTALLED_APPS.append("mwana.apps.webusers")
INSTALLED_APPS.append("mwana.apps.graphs")
INSTALLED_APPS.append("mwana.apps.surveillance")
INSTALLED_APPS.append("mwana.apps.zm_languages")
INSTALLED_APPS.append("mwana.apps.reminders.experimental")
INSTALLED_APPS.append("mwana.apps.errorhandling")

INSTALLED_APPS.insert(0, 'mwana.apps.blacklist')

ADMINS = (
          ('Trevor Sinkala', 'sinkalation@gmail.com'),
          )

MANAGERS = ADMINS

EMAIL_SUBJECT_PREFIX = '[Mwana] '
EMAIL_HOST = 'localhost'
DEFAULT_FROM_EMAIL = 'sinkalation@gmail.com'



TIME_ZONE = 'Africa/Lusaka'

LANGUAGE_CODE = 'en'
LANGUAGES = (
             ('bem', _('Bemba')),
             ('ton', _('Tonga')),
             ('en', _('English')),
             ('nya', _('Nyanja')),
             )

LOCATION_CODE_CLASS = 'mwana.zambia.locations.LocationCode'

ROOT_URLCONF = 'mwana.zambia.urls'

# LOG_FORMAT override to include time
LOG_FORMAT  = "[%(asctime)s] [%(name)s]: %(message)s"

#--------------Zambia Tab overrides---------------
# this rapidsms-specific setting defines which views are linked by the
# tabbed navigation. when adding an app to INSTALLED_APPS, you may wish
# to add it here, also, to expose it in the rapidsms ui.
RAPIDSMS_TABS = [
#    ('rapidsms.views.dashboard', 'Dashboard'),
#    ('rapidsms.contrib.httptester.views.generate_identity', 'Message Tester'),
#    ('mwana.apps.locations.views.dashboard', 'Map'),
#    ('rapidsms.contrib.messagelog.views.message_log', 'Message Log'),
#    ('rapidsms.contrib.messaging.views.messaging', 'Messaging'),
#    ('rapidsms.contrib.registration.views.registration', 'Registration'),
#    ('rapidsms.contrib.scheduler.views.index', 'Event Scheduler'),
#    ('mwana.apps.supply.views.dashboard', 'Supplies'),
#    ('mwana.apps.labresults.views.dashboard', 'Results160'),
    ('mwana.apps.reports.views.home', 'Home'),
    ('mwana.apps.reports.views.zambia_reports', 'Reports'),
    ('mwana.apps.alerts.views.mwana_alerts', 'Alerts'),
    ('mwana.apps.filteredlogs.views.filtered_logs', 'Logs'),
    ('mwana.apps.reports.views.supported_sites', 'Sites'),
    ('mwana.apps.reports.views.contacts_report', 'SMS Users'),
    ('mwana.apps.webusers.views.webusers', 'Web Users'),
#    ('mwana.apps.issuetracking.views.list_issues', 'Issues'),
    ('mwana.apps.websmssender.views.send_sms', 'Message Blaster'),
    ('mwana.apps.training.views.trained', 'Trained'),
    ('mwana.apps.graphs.views.graphs', 'Charts'),
    ('mwana.apps.surveillance.views.surveillance', 'Survey'),
#    ('mwana.apps.blacklist.views.blacklisted', 'Blacklisted People'),
]

ADH_LAB_NAME = "ADH DNA-PCR LAB"

SESSION_COOKIE_AGE = 3600 # 1 hour

# These URL will not require login
EXCLUDE_FROM_LOGIN = ['', '/home', '/', '/home/']
