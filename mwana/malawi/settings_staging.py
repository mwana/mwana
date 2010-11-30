from mwana.malawi.settings_country import *

DEBUG = False

ADMINS = (
    ('Tobias McNulty', 'mwana@caktusgroup.com'),
    ('Lengani Kaunda', 'lengani@p4studio.com'),
)

MANAGERS = ADMINS

EMAIL_SUBJECT_PREFIX = '[mwana-malawi-staging] '
EMAIL_HOST = 'localhost'
DEFAULT_FROM_EMAIL = 'no-reply@projectmwana.org'

XFORMS_HOST = 'malawi-qa.projectmwana.org'

# Modify INSTALLED_APPS if you like, e.g., add an app that disables the project
# only on the staging or production server, so that development can continue
# locally:
#INSTALLED_APPS.insert(INSTALLED_APPS.index("rapidsms"),
#                      "mwana.apps.whitelist")
#WHITELIST_RESPONSE = "I'm sorry, Results160 and RemindMi are still in testing "\
#                     "phase. We will notify you when the system is live."

# You can also customize RAPIDSMS_TABS like so:
RAPIDSMS_TABS.remove(('rapidsms.views.dashboard', 'Dashboard'))

# Add the pygsm backend for our MultiTech modem to INSTALLED_BACKENDS
#INSTALLED_BACKENDS.update({
#    "pygsm" : {"ENGINE": "rapidsms.backends.gsm",
#               "port": "/dev/ttyUSB0",
#               'baudrate': '115200',
#               'rtscts': '1',
#               'timeout': 10}
#})

# Add the kannel backends for Zain and TNM
INSTALLED_BACKENDS.update({
    "zain" : {
        "ENGINE":  "mwana.backends.kannel",
        "host": "127.0.0.1",
        "port": 8081,
        "sendsms_url": "http://127.0.0.1:13013/cgi-bin/sendsms",
        "sendsms_params": {"smsc": "zain-modem", "username": "rapidsms",
                            "password": ""}, # set in localsettings.py
        "coding": 0,
        "charset": "ascii",
    },
    "tnm" : {
        "ENGINE":  "mwana.backends.kannel",
        "host": "127.0.0.1",
        "port": 8082,
        "sendsms_url": "http://127.0.0.1:13013/cgi-bin/sendsms",
        "sendsms_params": {"smsc": "tnm-smpp", "username": "rapidsms",
                            "password": ""}, # set in localsettings.py
        "coding": 0,
        "charset": "ascii",
    }
})

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "mwana_legacy_staging",
        "USER": "mwana",
        "PASSWORD": "", # configure in localsettings.py
        "HOST": "localhost",
        "TEST_DATABASE_NAME": "test_mwana_legacy_staging",
    }
}

SEND_LIVE_LABRESULTS = True
SEND_LIVE_BIRTH_REMINDERS = False

CACHE_BACKEND = 'memcached://127.0.0.1:11211/?timeout=60'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# Override the default log settings:
LOG_LEVEL = "DEBUG"
LOG_FILE = "/var/log/rapidsms/rapidsms.route.log"
DJANGO_LOG_FILE = "/var/log/rapidsms/rapidsms.django.log"
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s"
LOG_SIZE = 1000000 # in bytes
LOG_BACKUPS = 256     # number of logs to keep around

# Configure email-based logging for errors & exceptions:
from mwana.logconfig import init_email_handler
init_email_handler(EMAIL_HOST, DEFAULT_FROM_EMAIL, ADMINS,
                   EMAIL_SUBJECT_PREFIX, LOG_FORMAT)
