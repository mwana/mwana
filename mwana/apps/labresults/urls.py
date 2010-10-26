
from django.conf.urls.defaults import *
from mwana.apps.labresults import views


urlpatterns = patterns('',
    url(r"^$", views.dashboard, name="labresults_dashboard"),
    url(r"^incoming/$", views.accept_results, name="accept_results"),
    url(r"^logs/(\d+)/(.+)/$", views.log_viewer, name="lab_receiver_logs"),
    url(r"^logs/(\d+)/$", views.log_viewer, name="lab_receiver_logs"),
    url(r"^logs/$", views.log_viewer, name="lab_receiver_logs"),
)
