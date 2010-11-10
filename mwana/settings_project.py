#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8

# -------------------------------------------------------------------- #
#                        PROJECT CONFIGURATION                         #
# -------------------------------------------------------------------- #
# Note that this file should only contain settings that can be shared
# across the entire project (i.e., in both Malawi and Zambia).
#
# Customization for a country or specific server environment should be done
# in the mwana/malawi/ or mwana/zambia/ directories, respectively.


# the rapidsms backend configuration is designed to resemble django's
# database configuration, as a nested dict of (name, configuration).
#
# the ENGINE option specifies the module of the backend; the most common
# backend types (for a GSM modem or an SMPP server) are bundled with
# rapidsms, but you may choose to write your own.
#
# all other options are passed to the Backend when it is instantiated,
# to configure it. see the documentation in those modules for a list of
# the valid options for each.
INSTALLED_BACKENDS = {
    #"att": {
    #    "ENGINE": "rapidsms.backends.gsm",
    #    "PORT": "/dev/ttyUSB0"
    #},
    #"verizon": {
    #    "ENGINE": "rapidsms.backends.gsm,
    #    "PORT": "/dev/ttyUSB1"
    #},
    "message_tester": {
        "ENGINE": "rapidsms.backends.bucket",
    }
}


# to help you get started quickly, many django/rapidsms apps are enabled
# by default. you may wish to remove some and/or add your own.
INSTALLED_APPS = [
    "mwana.apps.broadcast",
    #'south',
    # the essentials.
    "django_nose",
    "djtables",
    "rapidsms",

    # common dependencies (which don't clutter up the ui).
    "rapidsms.contrib.handlers",
    "rapidsms.contrib.ajax",

    # enable the django admin using a little shim app (which includes
    # the required urlpatterns), and a bunch of undocumented apps that
    # the AdminSite seems to explode without.
    "django.contrib.sites",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.contenttypes",

    # the rapidsms contrib apps.
    "rapidsms.contrib.export",
    "rapidsms.contrib.httptester",
#    "mwana.apps.locations",
    "rapidsms.contrib.messagelog",
    "rapidsms.contrib.messaging",
#    "rapidsms.contrib.registration",
    "rapidsms.contrib.scheduler",
    "rapidsms.contrib.echo",
    "mwana.apps.stringcleaning",
    "mwana.apps.contactsplus",
    "mwana.apps.registration",
    "mwana.apps.agents",
    "mwana.apps.labresults",
    "mwana.apps.reminders",
#    "mwana.apps.birth_reminders",
    "mwana.apps.location_importer",
#    "mwana.apps.supply",
    "mwana.apps.broadcast",
    "mwana.apps.reports",
    "mwana.apps.training",
    "mwana.apps.help",
    "mwana.apps.alerts",
    "mwana.apps.locations",

# This app should always come last to prevent it from hijacking other apps that handle default messages
    "rapidsms.contrib.default",
]

# this rapidsms-specific setting defines which views are linked by the
# tabbed navigation. when adding an app to INSTALLED_APPS, you may wish
# to add it here, also, to expose it in the rapidsms ui.
RAPIDSMS_TABS = [
    ('rapidsms.views.dashboard', 'Dashboard'),
    ('rapidsms.contrib.httptester.views.generate_identity', 'Message Tester'),
    ('mwana.apps.locations.views.dashboard', 'Map'),
    ('rapidsms.contrib.messagelog.views.message_log', 'Message Log'),
    ('rapidsms.contrib.messaging.views.messaging', 'Messaging'),
#    ('rapidsms.contrib.registration.views.registration', 'Registration'),
    ('rapidsms.contrib.scheduler.views.index', 'Event Scheduler'),
#    ('mwana.apps.supply.views.dashboard', 'Supplies'),
    ('mwana.apps.labresults.views.dashboard', 'Results160'),
    ('mwana.apps.labresults.views.mwana_reports', 'Reports'),
    ('mwana.apps.alerts.views.mwana_alerts', 'Alerts'),
]


# TODO: make a better default response, include other apps, and maybe 
# this dynamic?
DEFAULT_RESPONSE = "Invalid Keyword. Valid keywords are JOIN, AGENT, CHECK, RESULT, SENT, ALL, CBA, BIRTH and CLINIC. Respond with any keyword or HELP for more information."


# -------------------------------------------------------------------- #
#                         BORING CONFIGURATION                         #
# -------------------------------------------------------------------- #


# debug mode is turned on as default, since rapidsms is under heavy
# development at the moment, and full stack traces are very useful
# when reporting bugs. don't forget to turn this off in production.
DEBUG = TEMPLATE_DEBUG = True


# after login (which is handled by django.contrib.auth), redirect to the
# dashboard rather than 'accounts/profile' (the default).
LOGIN_REDIRECT_URL = "/"


# use django-nose to run tests. rapidsms contains lots of packages and
# modules which django does not find automatically, and importing them
# all manually is tiresome and error-prone.
TEST_RUNNER = "django_nose.NoseTestSuiteRunner"


# for some reason this setting is blank in django's global_settings.py,
# but it is needed for static assets to be linkable.
MEDIA_URL = "/static/"


# URL for admin media (also defined in apache configuration)
ADMIN_MEDIA_PREFIX = '/admin-media/'


# this is required for the django.contrib.sites tests to run, but also
# not included in global_settings.py, and is almost always ``1``.
# see: http://docs.djangoproject.com/en/dev/ref/contrib/sites/
SITE_ID = 1


# the default log settings are very noisy.
LOG_LEVEL   = "DEBUG"
LOG_FILE    = "logs/rapidsms.log"
LOG_FORMAT  = "[%(name)s]: %(message)s"
LOG_SIZE    = 8192 # 8192 bytes = 64 kb
LOG_BACKUPS = 256 # number of logs to keep
DJANGO_LOG_FILE  = 'logs/django.log'

# these weird dependencies should be handled by their respective apps,
# but they're not, so here they are. most of them are for django admin.
TEMPLATE_CONTEXT_PROCESSORS = [
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
]


# these apps should not be started by rapidsms in your tests, however,
# the models and bootstrap will still be available through django.
TEST_EXCLUDED_APPS = [
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rapidsms",
    "rapidsms.contrib.ajax",
    "rapidsms.contrib.httptester",
]


# the default ROOT_URLCONF module, bundled with rapidsms, detects and
# maps the urls.py module of each app into a single project urlconf.
# this is handy, but too magical for the taste of some. (remove it?)
#ROOT_URLCONF = "rapidsms.djangoproject.urls"
ROOT_URLCONF = "mwana.urls"


# For Schema Migration
SOUTH_MIGRATION_MODULES = {
    'rapidsms': 'testextensions_main.migrations',
}


# -------------------------------------------------------------------- #
#                       RESULTS160 CONFIGURATION                       #
# -------------------------------------------------------------------- #

# Results160 setting to configure whether or not real results from the lab
# should be delivered to health clinics
SEND_LIVE_LABRESULTS = True

# Miscellaneous slugs needed by Results160 and dependent on the data schema/
# local environment.  You will almost certainly want to customize these in
# your country-level settings file.
RESULTS160_SLUGS = {
# contact types:
    'CBA_SLUG': 'cba',
    'PATIENT_SLUG': 'patient',
    'CLINIC_WORKER_SLUG': 'clinic-worker',
    'DISTRICT_WORKER_SLUG': 'district-worker',
# location types:
    'CLINIC_SLUGS': ('clinic',),
    'ZONE_SLUGS': ('zone',),
    'DISTRICT_SLUGS': ('district',),
}

# -------------------------------------------------------------------- #
#                        REMINDMI CONFIGURATION                        #
# -------------------------------------------------------------------- #

# RemindMi setting to configure ...
SEND_LIVE_BIRTH_REMINDERS = True
