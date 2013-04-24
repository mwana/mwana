# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.graphs import views

urlpatterns = patterns('',
    url(r"^$", views.graphs, name="graphs"),
    url(r"^lab_submissions/$", views.lab_submissions, name="lab_submissions"),
    url(r"^monthly_lab_submissions/$", views.monthly_lab_submissions, name="monthly_lab_submissions"),
    url(r"^facility_vs_community/$", views.facility_vs_community, name="facility_vs_community"),
    url(r"^turnaround/$", views.turnaround, name="turnaround"),
)
