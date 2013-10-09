# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls import patterns, url
from mwana.apps.alerts import views


urlpatterns = patterns(
    '',
    url(r"^$", views.mwana_alerts, name="mwana_alerts"),
)
