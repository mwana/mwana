# vim: ai ts=4 sts=4 et sw=4
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

TEMPLATE_DIRS = (
    "/home/mwana/staging-environment/code_root/mwana/malawi/templates",)

#XFORMS_HOST = 'malawi-qa.projectmwana.org'

# Modify INSTALLED_APPS if you like, e.g., add an app that disables the project
# only on the staging or production server, so that development can continue
# locally:
#INSTALLED_APPS.insert(INSTALLED_APPS.index("rapidsms"),
#                      "mwana.apps.whitelist")
#WHITELIST_RESPONSE = "I'm sorry, Results160 and RemindMi are still in testing "\
#                     "phase. We will notify you when the system is live."

#DEFAULT_RESPONSE = "Invalid Keyword. Keywords are GM for Growth Monitor, MWANA for RemindMi, ALL for Broadcast and CHECK or RESULT for Results160. Send HELP for more information"

# Add the kannel backends for Airtel and TNM
# INSTALLED_BACKENDS.update({
#     "airtel": {
#         "ENGINE":  "rapidsms.backends.kannel",
#         "sendsms_url": "http://127.0.0.1:13013/cgi-bin/sendsms",
#         "sendsms_params": {"smsc": "zain-modem",
#                            "from": "+265999279085",  # will be overridden; set for consistency
#                            "username": "rapidsms",
#                            "password": ""},  # set password in localsettings.py
#         "coding": 0,
#         "charset": "ascii",
#         "encode_errors": "ignore",  # strip out unknown (unicode) characters
#         "delivery_report_url": "http://127.0.0.1:8000",
#     },
#     "tnm": {
#         "ENGINE":  "rapidsms.backends.kannel",
#         "sendsms_url": "http://127.0.0.1:13013/cgi-bin/sendsms",
#         "sendsms_params": {"smsc": "tnm-smpp",
#                            "from": "88160",  # not set automatically by SMSC
#                            "username": "rapidsms",
#                            "password": ""},  # set password in localsettings.py
#         "coding": 0,
#         "charset": "ascii",
#         "encode_errors": "ignore",  # strip out unknown (unicode) characters
#         "delivery_report_url": "http://127.0.0.1:8000",
#     }
# })

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "mwana_legacy_staging",
        "USER": "mwana",
        "PASSWORD": "",  # configure in localsettings.py
        "HOST": "127.0.0.1",
        "PORT": "5433",
        "TEST_DATABASE_NAME": "test_mwana_legacy_staging",
    }
}

SEND_LIVE_LABRESULTS = False
SEND_LIVE_BIRTH_REMINDERS = False

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# CACHE_BACKEND = 'memcached://127.0.0.1:11211/?timeout=60'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# Override the default log settings:
LOG_LEVEL = "DEBUG"
LOG_FILE = "/var/log/rapidsms/rapidsms.route.log"
DJANGO_LOG_FILE = "/var/log/rapidsms/rapidsms.django.log"
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s"
LOG_SIZE = 1000000  # in bytes
LOG_BACKUPS = 256     # number of logs to keep around

# Configure email-based logging for errors & exceptions:
from mwana.logconfig import init_email_handler
init_email_handler(EMAIL_HOST, DEFAULT_FROM_EMAIL, ADMINS,
                   EMAIL_SUBJECT_PREFIX, LOG_FORMAT)
