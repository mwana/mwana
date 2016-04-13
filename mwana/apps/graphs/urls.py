# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.graphs import views

urlpatterns = patterns('',
    url(r"^$", views.graphs, name="graphs"),
    url(r"^lab_submissions/$", views.lab_submissions, name="lab_submissions"),
    url(r"^monthly_lab_submissions/$", views.monthly_lab_submissions, name="monthly_lab_submissions"),
    url(r"^facility_vs_community/$", views.facility_vs_community, name="facility_vs_community"),
    url(r"^turnaround/$", views.turnaround, name="turnaround"),
    url(r"^messages/$", views.messages, name="messages"),
    url(r"^messages_by_user_type/$", views.messages_by_user_type, name="messages_by_user_type"),
    url(r"^messages_by_location/$", views.messages_by_location, name="messages_by_location"),
    url(r"^monthly_birth_trends/$", views.monthly_birth_trends, name="monthly_birth_trends"),
    url(r"^monthly_turnaround_trends/$", views.monthly_turnaround_trends, name="monthly_turnaround_trends"),
    url(r"^monthly_results_retrival_trends/$", views.monthly_results_retrival_trends, name="monthly_results_retrival_trends"),
    url(r"^monthly_scheduled_visit_trends/$", views.monthly_scheduled_visit_trends, name="monthly_scheduled_visit_trends"),
    url(r"^dbs_testing_trends/$", views.dbs_testing_trends, name="dbs_testing_trends"),
)
