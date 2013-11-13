# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls.defaults import *
from mwana.apps.reports import views
from smscouchforms.views import download as home
from mwana.apps.smgl.views import home_page

urlpatterns = patterns('',
    # global project URLs:
    (r'^', include('mwana.urls')),
    # custom URL additions for Zambia:
    url(r'^$', home_page, name='home'),
    url(r'^contacts/', views.contacts_report, name='mwana_contacts'),
    (r'^logs/', include('mwana.apps.filteredlogs.urls')),
)
