# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls import patterns, url
from mwana.apps.echo import views

urlpatterns = patterns(
    '',
    url(r"^$", views.index, name="labresults_dashboard"))
