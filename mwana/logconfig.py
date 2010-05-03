from mwana import prod_settings


def init_django_logging():
    """
    Initializes logging for the Django side of RapidSMS, using a little hack
    to ensure that it only gets initialized once.  Derived from:
    
    http://stackoverflow.com/questions/342434/python-logging-in-django
    
    This is necessary if the logging is initialized in settings.py, but it
    may not be if it's initialized through project.wsgi.  Logging can't be
    initialized in the settings file because the route process also uses
    settings and sets up its own logging in the management command.
    """
    import logging.handlers
    root_logger = logging.getLogger()
    if getattr(root_logger, 'django_log_init_done', False):
        return
    root_logger.django_log_init_done = True
    file_handler = logging.handlers.RotatingFileHandler(
              prod_settings.DJANGO_LOG_FILE, maxBytes=prod_settings.LOG_SIZE,
              backupCount=prod_settings.LOG_BACKUPS)
    root_logger.setLevel(getattr(logging, prod_settings.LOG_LEVEL))
    file_handler.setFormatter(logging.Formatter(prod_settings.LOG_FORMAT))
    root_logger.addHandler(file_handler)
    logger = logging.getLogger(__name__)
    logger.info('logger initialized')
