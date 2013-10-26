#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8
import os
# -------------------------------------------------------------------- #
#                        PROJECT CONFIGURATION                         #
# -------------------------------------------------------------------- #
# Note that this file should only contain settings that can be shared
# across the entire project (i.e., in both Malawi and Zambia).
#
# Customization for a country or specific server environment should be done
# in the mwana/malawi/ or mwana/zambia/ directories, respectively.

# The top directory for this project.
# PROJECT_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# The country level directory with that country project's templates,
# settings, urls, static dir, wsgi.py, fixtures, etc.
# PROJECT_PATH = os.path.join(PROJECT_ROOT, '<country>')

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
        "ENGINE": "rapidsms.backends.database.DatabaseBackend",
    }
}


# to help you get started quickly, many django/rapidsms apps are enabled
# by default. you may wish to remove some and/or add your own.
INSTALLED_APPS = [
    "mwana.apps.broadcast",
    # this has to come before the handlers app because of the CONFIRM handler
    # in patienttracing
    "mwana.apps.tlcprinters",
    "mwana.apps.labresults",
    'south',
    # the essentials.
    "django_nose",
    "django_tables2",
    "selectable",
    "djtables",
    "rapidsms",
    "rapidsms.backends.kannel",
    "rapidsms.backends.database",
    "rapidsms.router.db",
    "djcelery",
    "kombu.transport.django",
    # common dependencies (which don't clutter up the ui).
    "rapidsms.contrib.handlers",
    # enable the django admin using a little shim app (which includes
    # the required urlpatterns), and a bunch of undocumented apps that
    # the AdminSite seems to explode without.
    "django.contrib.sites",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    # the rapidsms contrib apps.
    "rapidsms.contrib.httptester",
    "rapidsms.contrib.messagelog",
    "rapidsms.contrib.messaging",
    "mwana.apps.contactsplus",
    "mwana.apps.registration",
    "mwana.apps.agents",
    "mwana.apps.reminders",
    "mwana.apps.location_importer",
    "mwana.apps.reports",
    "mwana.apps.training",
    "mwana.apps.help",
    "mwana.apps.alerts",
    "mwana.apps.locations",
    "mwana.apps.patienttracing",
    "mwana.apps.hub_workflow",
    "mwana.apps.stringcleaning",
    "mwana.apps.translator",
    # This app should always come last to prevent it from
    # hijacking other apps that handle default messages
    "rapidsms.contrib.default",
]

# TODO: make a better default response, include other apps, and maybe
# this dynamic?
# DEFAULT_RESPONSE = '''Invalid Keyword. Valid keywords are JOIN, AGENT, CHECK,
# RESULT, SENT, ALL, CBA, BIRTH and CLINIC. Respond with any keyword or HELP for
# more information.'''


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
#TEST_RUNNER = "django_nose.NoseTestSuiteRunner"

# URL for admin media (also defined in apache configuration)
ADMIN_MEDIA_PREFIX = '/admin-media/'


# this is required for the django.contrib.sites tests to run, but also
# not included in global_settings.py, and is almost always ``1``.
# see: http://docs.djangoproject.com/en/dev/ref/contrib/sites/
SITE_ID = 1


# the default log settings are very noisy.
# LOG_LEVEL = "DEBUG"
# LOG_FILE = "logs/rapidsms.log"
# LOG_FORMAT = "[%(name)s]: %(message)s"
# LOG_SIZE = 8192  # 8192 bytes = 64 kb
# LOG_BACKUPS = 256  # number of logs to keep
# DJANGO_LOG_FILE = 'logs/django.log'


# A sample logging configuration.
# This logs all rapidsms messages to the file `rapidsms.log`
# in the project directory.  It also sends an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'basic': {
            'format': '%(asctime)s %(name)-20s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'basic',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'basic',
            'filename': os.path.join(PROJECT_ROOT, 'logs', 'rapidsms.log'),
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'rapidsms': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'mwana.middleware.LoginRequired',
]


# these weird dependencies should be handled by their respective apps,
# but they're not, so here they are. most of them are for django admin.
TEMPLATE_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "django.core.context_processors.csrf",
    'django.core.context_processors.static',
]

TEMPLATE_DIRS = (os.path.join(PROJECT_ROOT, "templates"),)

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/public/media/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'public', 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/public/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'public', 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files to collect
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# these apps should not be started by rapidsms in your tests, however,
# the models and bootstrap will still be available through django.
TEST_EXCLUDED_APPS = [
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rapidsms",
    # "rapidsms.contrib.ajax",
    # "rapidsms.contrib.httptester",
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


# The maximum length of an SMS to be sent through the system.  It is only
# enforced manually; i.e., you need to use it to chunk your messages
# appropriately.
MAX_SMS_LENGTH = 160


# -------------------------------------------------------------------- #
#                       RESULTS160 CONFIGURATION                       #
# -------------------------------------------------------------------- #

# Results160 setting to configure whether or not real results from the lab
# should be delivered to health clinics
SEND_LIVE_LABRESULTS = True

# When set to True, incoming messages from non-standard phone numbers will be
# ignored. E.g. +551, MTN, 440. See handle()in stringcleaning app.py
ON_LIVE_SERVER = False

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
