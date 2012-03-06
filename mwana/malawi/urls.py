# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls.defaults import *
from mwana.apps.reports import views

urlpatterns = patterns('',
    # global project URLs:
    (r'^', include('mwana.urls')),
    # custom URL additions for Malawi:
    url(r'^$', views.malawi_home, name='mwana_home'),
    url(r'^results160', views.malawi_reports, name='mwana_reports'),
    url(r"^csv/report-one/",  views.csv_report_one, name="csv_report_one"),
    url(r"^csv/report-two/",  views.csv_report_two, name="csv_report_two"),
    (r'^', include('rapidsms_xforms.urls')), # needs top level formList url
    (r'^growth/', include('mwana.apps.nutrition.urls')),
)
