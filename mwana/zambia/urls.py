# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls.defaults import *
from mwana.apps.reports import views

urlpatterns = patterns('',
    # global project URLs:
    (r'^', include('mwana.urls')),
    # custom URL additions for Zambia:
    url(r'^$', views.zambia_reports, name='mwana_reports'),
    url(r'^contacts/', views.contacts_report, name='mwana_contacts'),
    url(r'^groups/', views.group_facility_mapping, name='group_facility_mapping'),
    (r'^logs/', include('mwana.apps.filteredlogs.urls')),
    (r'^issues/', include('mwana.apps.issuetracking.urls')),
)
