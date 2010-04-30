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

def init_django_logging():
    """
    Initializes logging for the Django side of RapidSMS, using a little hack
    to ensure that it only gets initialized once.  Derived from:
    
    http://stackoverflow.com/questions/342434/python-logging-in-django
    """
    import logging.handlers
    root_logger = logging.getLogger()
    if getattr(root_logger, 'django_log_init_done', False):
        return
    root_logger.django_log_init_done = True
    file_handler = logging.handlers.RotatingFileHandler(
              DJANGO_LOG_FILE, maxBytes=LOG_SIZE,
              backupCount=LOG_BACKUPS)
    root_logger.setLevel(getattr(logging, LOG_LEVEL))
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(file_handler)
    logger = logging.getLogger(__name__)
    logger.info('logger initialized')

init_django_logging()
