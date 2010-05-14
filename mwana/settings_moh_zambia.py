from mwana.settings import *

# temporarily disable the entire project in the production environment
# until we get approval
INSTALLED_APPS.insert(INSTALLED_APPS.index("rapidsms"),
                      "mwana.apps.whitelist")
WHITELIST_RESPONSE = "I'm sorry, Results160 and RemindMi are still in testing "\
                     "phase. We will notify you when the system is live."
SEND_LIVE_LABRESULTS = False

DEBUG = False

ADMINS = (
    ('Tobias McNulty', 'tobias@caktusgroup.com'),
    ('Drew Roos', 'droos@dimagi.com'),
    ('Mwana Developers', 'mwana-dev@googlegroups.com'),
)

MANAGERS = ADMINS

EMAIL_SUBJECT_PREFIX = '[Mwana] '
EMAIL_HOST = 'localhost'
DEFAULT_FROM_EMAIL = 'no-reply@unicefinnovation.org'

TIME_ZONE = 'Africa/Lusaka'

LANGUAGE_CODE = 'bem-zm'

INSTALLED_BACKENDS.update({
    "pygsm" : {"ENGINE": "rapidsms.backends.gsm",
               "port": "/dev/ttyUSB0",
               'baudrate': '115200', 
               'rtscts': '1',
               'timeout': 10}
})

CACHE_BACKEND = 'memcached://127.0.0.1:11211/?timeout=60'

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# Override the default log settings
LOG_LEVEL = "DEBUG"
LOG_FILE = "/var/log/rapidsms/rapidsms.route.log"
DJANGO_LOG_FILE = "/var/log/rapidsms/rapidsms.django.log"
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s"
LOG_SIZE = 1000000 # in bytes
LOG_BACKUPS = 256     # number of logs to keep around

from mwana.logconfig import init_email_handler
init_email_handler(EMAIL_HOST, DEFAULT_FROM_EMAIL, ADMINS,
                   EMAIL_SUBJECT_PREFIX, LOG_FORMAT)
