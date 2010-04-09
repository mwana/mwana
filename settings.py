#!/usr/bin/env python
# vim: et ts=4 sw=4


# inherit everything from rapidsms, as default
# (this is optional. you can provide your own.)
from rapidsms.djangoproject.settings import *


# then add your django settings:

DATABASE_ENGINE = "sqlite3"
DATABASE_NAME = "db.sqlite3"

INSTALLED_APPS = (
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.admin",
    "rapidsms",
    "rapidsms.contrib.ajax", 
    "rapidsms.contrib.httptester", 
    "rapidsms.contrib.handlers", 
    "rapidsms.contrib.echo",
    "rapidsms.contrib.messagelog",
    "rapidsms.contrib.registration",

    # enable the django admin using a little shim app (which includes
    # the required urlpatterns)
    "rapidsms.contrib.djangoadmin",
    "django.contrib.admin",
)



INSTALLED_BACKENDS = {
    "message_tester" : {"ENGINE": "rapidsms.backends.bucket" } 
}
    

# TEMPLATE_DIRS = []
