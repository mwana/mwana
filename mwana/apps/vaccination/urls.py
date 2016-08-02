# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.vaccination import views


urlpatterns = patterns('',
    url(r"^$", views.dashboard, name="vaccination_dashboard"),
)
