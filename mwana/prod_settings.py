from mwana.settings import *

DEBUG = False

ADMINS = (
    ('Tobias McNulty', 'tobias@caktusgroup.com'),
    ('Mwana Developers', 'mwana-dev@googlegroups.com'),
)

MANAGERS = ADMINS

EMAIL_SUBJECT_PREFIX = '[Mwana] '
DEFAULT_FROM_EMAIL = 'no-reply@unicefinnovation.org'

TIME_ZONE = 'GMT+2'

INSTALLED_BACKENDS.update({
    "pygsm" : {"ENGINE": "rapidsms.backends.gsm",
               "port": "/dev/ttyUSB0",
               'baudrate': '115200', 
               'rtscts': '1',
               'timeout': 10}
})

# Override the default log settings
LOG_LEVEL = "DEBUG"
LOG_FILE = "/var/log/rapidsms/rapidsms.route.log"
DJANGO_LOG_FILE = "/var/log/rapidsms/rapidsms.django.log"
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s"
LOG_SIZE = 1000000 # in bytes
LOG_BACKUPS = 256     # number of logs to keep around
