# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.blacklist import views


urlpatterns = patterns('',
    url(r"^$", views.blacklisted, name="blacklisted"),
)
