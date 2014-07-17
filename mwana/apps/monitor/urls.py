# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.monitor import views


urlpatterns = patterns('',
    url(r"^$", views.data_integrity_issues, name="data_integrity_issues"),
)
