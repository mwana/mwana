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

TIME_ZONE = 'GMT+2'

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

import hashlib
import logging.handlers

class EmailMsgFormatter(logging.Formatter):
    
    def format(self, record):
        """
        Extends the parent's format with a traceback at the end.
        """
        import pprint
        import traceback
        pp = pprint.PrettyPrinter(indent=4)
        # remove 9 lines from the end of traceback, which are all standard
        # logging module code
        stack = '\n'.join(traceback.format_list(traceback.extract_stack())[:-9])

        return logging.Formatter.format(self, record) + """

Traceback:
%s

Full log record:
%s""" % (stack, pp.pformat(record.__dict__))


class RateLimitingSMTPHandler(logging.handlers.SMTPHandler):
    
    timeout = 3600
    
    def emit(self, record):
        """
        Silently drops log records that have been sent with the past
        ``self.timeout`` seconds.  Uses a hash of the message text, level,
        file path, and line number as a key to determine if the message has
        already been sent.
        """
        from django.core.cache import cache
        m = hashlib.md5()
        m.update(record.pathname)
        m.update(str(record.lineno))
        m.update(record.msg)
        m.update(record.levelname)
        cache_key = 'mwana-log-' + m.hexdigest()
        if not cache.get(cache_key):
            cache.set(cache_key, True, self.timeout)
            logging.handlers.SMTPHandler.emit(self, record)


def init_email_handler():
    """
    Adds an email handler for errors and warnings, using a little hack
    to ensure that it only gets initialized once.  Derived from:
    
    http://stackoverflow.com/questions/342434/python-logging-in-django
    
    This is in settings because settings is loaded by both the route process
    and the wsgi process(es), and we want to email errors from both processes.
    There's also no other place (that I know of) to successfully add a handler
    to the route process, without monkey patching the route command itself.
    """
    root_logger = logging.getLogger()
    if getattr(root_logger, 'email_handler_log_init_done', False):
        return
    root_logger.email_handler_log_init_done = True
    smtp = RateLimitingSMTPHandler(EMAIL_HOST,
                                   DEFAULT_FROM_EMAIL,
                                   [email for name, email in ADMINS],
                                   EMAIL_SUBJECT_PREFIX + 'log message')
    smtp.getSubject = lambda record: EMAIL_SUBJECT_PREFIX + record.levelname +\
                                     ': ' + record.msg
    smtp.setLevel(logging.ERROR)
    smtp.setFormatter(EmailMsgFormatter(LOG_FORMAT))
    root_logger.addHandler(smtp)
    logger = logging.getLogger(__name__)
    logger.info('email handler added')

init_email_handler()
