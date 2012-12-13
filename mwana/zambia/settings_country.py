# vim: ai ts=4 sts=4 et sw=4
from mwana.settings_project import *

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
    'CLINIC_SLUGS': ('urban_health_centre', '1st_level_hospital',
                    'rural_health_centre', 'health_post'),
    'ZONE_SLUGS': ('zone',),
    'DISTRICT_SLUGS': ('districts',),  # XXX verify me
    'PROVINCE_SLUGS': ('provinces',),  # XXX verify me
}
INSTALLED_APPS.append("mwana.apps.reports.webreports")
INSTALLED_APPS.append("mwana.apps.userverification")
#INSTALLED_APPS.append("mwana.apps.errorhandling")
INSTALLED_APPS.append("mwana.apps.filteredlogs")
INSTALLED_APPS.append("mwana.apps.monitor")
INSTALLED_APPS.append("mwana.apps.websmssender")
INSTALLED_APPS.append("mwana.apps.issuetracking")
INSTALLED_APPS.append("mwana.apps.email")

ADMINS = (
    ('Trevor Sinkala', 'sinkalation@gmail.com'),
)

MANAGERS = ADMINS

EMAIL_SUBJECT_PREFIX = '[Mwana] '
EMAIL_HOST = 'localhost'
DEFAULT_FROM_EMAIL = 'sinkalation@gmail.com'

TIME_ZONE = 'Africa/Lusaka'

LANGUAGE_CODE = 'to-zm'

LOCATION_CODE_CLASS = 'mwana.zambia.locations.LocationCode'

ROOT_URLCONF = 'mwana.zambia.urls'

# LOG_FORMAT override to include time
LOG_FORMAT = "[%(asctime)s] [%(name)s]: %(message)s"

#--------------Zambia Tab overrides---------------
# this rapidsms-specific setting defines which views are linked by the
# tabbed navigation. when adding an app to INSTALLED_APPS, you may wish
# to add it here, also, to expose it in the rapidsms ui.
RAPIDSMS_TABS = [
    ("mwana.apps.smgl.views.statistics",  "Statistics"),
    ('rapidsms.contrib.messagelog.views.message_log', 'Message Log'),
    ("mwana.apps.smgl.views.mothers",  "Mothers"),
    ("mwana.apps.smgl.views.referrals",  "Referrals & Notifications"),
    ("mwana.apps.smgl.views.sms_users",  "SMS Users"),
]

ADH_LAB_NAME = "ADH DNA-PCR LAB"


gettext = lambda s: s

LANGUAGES = (
             ('to', gettext('Tonga')),
             ('en', gettext('English'))
             )


