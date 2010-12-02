# vim: ai ts=4 sts=4 et sw=4
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


def init_email_handler(email_host, default_from_email, admins,
                       email_subject_prefix, log_format):
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
    smtp = RateLimitingSMTPHandler(email_host,
                                   default_from_email,
                                   [email for name, email in admins],
                                   email_subject_prefix + 'log message')
    smtp.getSubject = lambda record: ''.join([email_subject_prefix,
                                              record.levelname,
                                              ': ', record.msg])
    smtp.setLevel(logging.ERROR)
    smtp.setFormatter(EmailMsgFormatter(log_format))
    root_logger.addHandler(smtp)
    logger = logging.getLogger(__name__)
    logger.info('email handler added')


def init_file_logging(log_file, log_size, log_backups, log_level, log_format):
    """
    Initializes logging for the Django side of RapidSMS, using a little hack
    to ensure that it only gets initialized once.  Derived from:
    
    http://stackoverflow.com/questions/342434/python-logging-in-django
    
    This is necessary if the logging is initialized in settings.py, but it
    may not be if it's initialized through project.wsgi.  Logging can't be
    initialized in the settings file because the route process also uses
    settings and sets up its own logging in the management command.
    """
    root_logger = logging.getLogger()
    if getattr(root_logger, 'django_log_init_done', False):
        return
    root_logger.django_log_init_done = True
    file = logging.handlers.RotatingFileHandler(log_file,
                                                maxBytes=log_size,
                                                backupCount=log_backups)
    root_logger.setLevel(getattr(logging, log_level))
    file.setLevel(getattr(logging, log_level))
    file.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file)
    logger = logging.getLogger(__name__)
    logger.info('logger initialized')
