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
    'DISTRICT_SLUGS': ('districts',), # XXX verify me
    'PROVINCE_SLUGS': ('provinces',), # XXX verify me
}
INSTALLED_APPS.append("mwana.apps.reports.webreports")
TIME_ZONE = 'Africa/Lusaka'

LANGUAGE_CODE = 'bem-zm'

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
    ('mwana.apps.reports.views.zambia_reports', 'Reports'),
    ('mwana.apps.alerts.views.mwana_alerts', 'Alerts'),
]