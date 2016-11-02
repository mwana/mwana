# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.labtests import views
from mwana.apps.graphs import views as graph_views

urlpatterns = patterns('',
    url(r"^$", views.dashboard, name="dashboard"),
    url(r"^eid/$", views.eid_dashboard, name="eid_dashboard"),
    url(r"^dbs/$", views.eid_dashboard, name="eid_dashboard"),
    url(r"^graph/$", graph_views.trivial_graphs, name="graphs"),
    url(r"^graphs/$", graph_views.trivial_graphs, name="graphs"),
    url(r"^incoming/$", views.accept_results, name="accept_results"),
)

