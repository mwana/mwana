# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls.defaults import *
from mwana.apps.reports import views

urlpatterns = patterns('',
    # global project URLs:
    (r'^', include('mwana.urls')),
    # custom URL additions for Malawi:
    url(r'^$', views.malawi_reports, name='mwana_reports'),
    url(r'^csv/report1', views.csv_received, name='csv_received'),
    url(r'^csv/report2', views.csv_pending, name='csv_pending'),
    url(r'^csv/results', views.csv_results, name='csv_results'),
    (r'^', include('rapidsms_xforms.urls')), # needs top level
                       # formList url
)
