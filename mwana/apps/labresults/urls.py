
from django.conf.urls.defaults import *
from mwana.apps.labresults import views


urlpatterns = patterns('',
    url(r"^labresults/$", views.dashboard, name="labresults_dashboard"),
    url(r"^labresults/incoming/$", views.accept_results, name="accept_results"),
    url(r"^labresults/logs/(\d+)/(.+)/$", views.log_viewer, name="lab_receiver_logs"),
    url(r"^labresults/logs/(\d+)/$", views.log_viewer, name="lab_receiver_logs"),
    url(r"^labresults/logs/$", views.log_viewer, name="lab_receiver_logs"),
    url(r"^reports/$", views.mwana_reports, name="mwana_reports"),
)
