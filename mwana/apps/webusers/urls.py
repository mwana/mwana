# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.webusers import views


urlpatterns = patterns('',
    url(r"^$", views.webusers, name="webusers"),
)
