# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls.defaults import *
from mwana.apps.reports import views

urlpatterns = patterns('',
    # global project URLs:
    (r'^', include('mwana.urls')),
    # custom URL additions for Zambia:
    url(r'^$', views.home, name='home'),
    url(r'^reports/', views.zambia_reports, name='mwana_reports'),
    url(r'^contacts/', views.contacts_report, name='mwana_contacts'),
    url(r'^groups/', views.group_facility_mapping, name='group_facility_mapping'),
    url(r'^usergroups/', views.group_user_mapping, name='group_user_mapping'),
    url(r'^supported_sites/', views.supported_sites, name='supported_sites'),
    url(r'^home/', views.home, name='home'),
    (r'^logs/', include('mwana.apps.filteredlogs.urls')),
    (r'^issues/', include('mwana.apps.issuetracking.urls')),
    (r'^trained/', include('mwana.apps.training.urls')),
    (r'^blacklist/', include('mwana.apps.blacklist.urls')),
    (r'^webusers/', include('mwana.apps.webusers.urls')),
    (r'^graphs/', include('mwana.apps.graphs.urls')),
    (r'^charts/', include('mwana.apps.graphs.urls')),
)
