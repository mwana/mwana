# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.surveillance import views

urlpatterns = patterns('',
    url(r"^$", views.surveillance, name="surveillance"),
    url(r"^export_to_csv/$", views.export_to_csv, name="export_to_csv"),
)
