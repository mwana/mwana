#!/usr/bin/env python
import os
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
    "httptester": {
            "ENGINE": "threadless_router.backends.httptester.backend",
    },
}


# to help you get started quickly, many django/rapidsms apps are enabled
# by default. you may wish to remove some and/or add your own.
INSTALLED_APPS = [
    "dupechecker",  # needs to go near the front

    "threadless_router.backends.httptester",
    "threadless_router.backends.kannel",
    "rosetta",
    "mwana.apps.broadcast",
    # this has to come before the handlers app because of the CONFIRM handler
    # in patienttracing
    "mwana.apps.tlcprinters",
    'south',
    # the essentials.
    "django_nose",
    "soil",
    "djtables",
    "rapidsms",
    'taggit',

    # common dependencies (which don't clutter up the ui).
    "selectable",
    "rapidsms.contrib.ajax",
    "uni_form",
    "eav",
    'djcelery',
    'djkombu',

    # enable the django admin using a little shim app (which includes
    # the required urlpatterns), and a bunch of undocumented apps that
    # the AdminSite seems to explode without.
    "django.contrib.sites",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "touchforms.formplayer",

    "smsforms",
    "smscouchforms",
    "couchforms",
    "couchexport",
    "couchlog",


    # the rapidsms contrib apps.
    "rapidsms.contrib.export",
    "rapidsms.contrib.httptester",
    "mwana.apps.locations",
    "rapidsms.contrib.handlers",
    "rapidsms.contrib.messagelog",
    "rapidsms.contrib.messaging",
    #    "rapidsms.contrib.registration",
    "scheduler",
    # "scheduler",
    "mwana.apps.smgl",
    "mwana.apps.echo",
    "mwana.apps.contactsplus",
    "mwana.apps.registration",
    "mwana.apps.agents",
    "mwana.apps.broadcast",

    "mwana.apps.labresults",
    # "mwana.apps.reminders",
    # "mwana.apps.birth_reminders",
    "mwana.apps.location_importer",
    # "mwana.apps.supply",
    "mwana.apps.reports",
    "mwana.apps.training",
    "mwana.apps.help",
    "mwana.apps.alerts",

    # "mwana.apps.patienttracing",
    # "mwana.apps.hub_workflow",
    # "mwana.apps.stringcleaning",
# This app should always come last to prevent it from hijacking other apps that handle default messages
    "mwana.apps.default",
]

#TOUCHFORMS CONFIG
XFORMS_PLAYER_URL = "http://127.0.0.1:4444"

# this rapidsms-specific setting defines which views are linked by the
# tabbed navigation. when adding an app to INSTALLED_APPS, you may wish
# to add it here, also, to expose it in the rapidsms ui.
#RAPIDSMS_TABS = []    # SET ME IN COUNTRY/LOCALSETTINGS!
# this dynamic?

# for translations
_ = lambda x: x
DEFAULT_RESPONSE = _("Invalid keyword. Submit a form with a valid keyword: AMB, RESP, OUTC, REFER, REG, FUP, PP, BIRTH, DEATH, REFOUT, TOLD, LOOK, LEAVE or text HELP for assistance.")


# -------------------------------------------------------------------- #
#                         BORING CONFIGURATION                         #
# -------------------------------------------------------------------- #

SECRET_KEY = "SET_ME_TO_SOMETHING_UNIQUE"

# debug mode is turned on as default, since rapidsms is under heavy
# development at the moment, and full stack traces are very useful
# when reporting bugs. don't forget to turn this off in production.
DEBUG = TEMPLATE_DEBUG = True
TEMPLATE_DIRS = ('apps/smgl/templates/smgl/',)
BASE_TEMPLATE_SPLIT_2 = "layout-split-2.html"
BASE_TEMPLATE = "smgl/layout.html"
# after login (which is handled by django.contrib.auth), redirect to the
# dashboard rather than 'accounts/profile' (the default).
LOGIN_REDIRECT_URL = "/"


# use django-nose to run tests. rapidsms contains lots of packages and
# modules which django does not find automatically, and importing them
# all manually is tiresome and error-prone.
#TEST_RUNNER = "django_nose.NoseTestSuiteRunner"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder"
    )

SETTINGS_PATH = os.path.dirname(__file__)
FORMDESIGNER_PATH = os.path.join(SETTINGS_PATH, '..', 'submodules', 'vellum')

STATICFILES_DIRS = (
    ("formdesigner", FORMDESIGNER_PATH),
)
MEDIA_URL = "/media/"
MEDIA_ROOT = "../downloads"
STATIC_URL = "/static/"
STATIC_ROOT = "../STATICFILES/"
STATIC_DOC_ROOT = "../static_docs/"

## URL for admin media (also defined in apache configuration)
#ADMIN_MEDIA_PREFIX = '/admin-media/'


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
    "django.core.context_processors.debug",
    "django.core.context_processors.static",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "touchforms.context_processors.meta",
    "django.core.context_processors.csrf",
    "rapidsms.context_processors.logo",
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
    'DATA_ASSOCIATE_SLUG': 'da',
    'PATIENT_SLUG': 'patient',
    'CLINIC_WORKER_SLUG': 'clinic-worker',
    'DISTRICT_WORKER_SLUG': 'district-worker',
    'EMERGENCY_RESPONDER_SLUG': 'er',
    'AMBULANCE_DRIVER_SLUG' : 'ad',
    'TRIAGE_NURSE_SLUG' : 'tn',
# location types:
    'CLINIC_SLUGS': ('clinic',),
    'ZONE_SLUGS': ('zone',),
    'DISTRICT_SLUGS': ('district',),
    'RHC_SLUGS': ('rhc',),
    'UHC_SLUGS': ('uhc',),
}



# -------------------------------------------------------------------- #
#                        REMINDMI CONFIGURATION                        #
# -------------------------------------------------------------------- #

# RemindMi setting to configure ...
SEND_LIVE_BIRTH_REMINDERS = False

XFORMS_HOST = "localhost:8000"

FORMDESIGNER_PATH = "/path/to/formdesigner"

#Used by touchforms?
GMAPS_API_KEY = 'foo'
REVISION = '1.0'

######################################
## Set these in your localsettings!
#####################################

#COUCH_SERVER_ROOT='localhost:5984'
#COUCH_USERNAME=''
#COUCH_PASSWORD=''
#COUCH_DATABASE_NAME=''
####### Couch Forms & Couch DB Kit Settings #######
#def get_server_url(server_root, username, password):
#    if username and password:
#        return "http://%(user)s:%(pass)s@%(server)s" % {"user": username,
#                                                        "pass": password,
#                                                        "server": server_root }
#    else:
#        return "http://%(server)s" % {"server": server_root }
#
#COUCH_SERVER = get_server_url(COUCH_SERVER_ROOT, COUCH_USERNAME, COUCH_PASSWORD)
#
#COUCH_DATABASE = "%(server)s/%(database)s" % {"server": COUCH_SERVER, "database": COUCH_DATABASE_NAME }
#
#COUCHDB_DATABASES = [(app_label, COUCH_DATABASE) for app_label in COUCHDB_APPS]
#
#XFORMS_POST_URL = "%s/_design/couchforms/_update/xform/" % COUCH_DATABASE

#URLs listed here won't require logging in.  The match is done by using startswith(): if the current url starts
#with one of the items below, it's a match.
NO_LOGIN_REQUIRED_WHITELIST = [
    '/admin/',
    '/accounts/login/',
    '/accounts/logout/',
    '/labresults/incoming/',
    MEDIA_URL,
    '/backend/'
]



SITE_TITLE = "SMGL - Saving Mothers Giving Life"
LOGO_LEFT_URL = ''
LOGO_RIGHT_URL = ''

EXCLUDED_HANDLERS = ["mwana.apps.labresults"]

# multiple "empty" births can be registered with the same message
DUPECHECKER_IGNORE = ["birth none",
                      "look",
                      "help",
                      'in',
                      'out',
                      'join',
                      'leave',
                      'quit',
                      'back',
                     ]
