# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls.defaults import *
from mwana.apps.reports import views
from mwana.apps.reminders import views as remindmi

urlpatterns = patterns(
    '',
    # global project URLs:
    (r'^', include('mwana.urls')),
    # custom URL additions for Malawi:
    url(r'^$', views.dashboard_malawi, name='malawi_home'),
    url(r'^results160/graphs/', views.malawi_graphs, name='mwana_graphs'),
    url(r'^results160', views.malawi_reports, name='mwana_reports'),
    url(r"^csv/report-one/", views.csv_report_one, name="csv_report_one"),
    url(r"^csv/report-two/", views.csv_report_two, name="csv_report_two"),
    url(r"^csv/mother-count/", remindmi.csv_mother_count, name="csv_mother_count"),
    url(r"^csv/child-count/", remindmi.csv_child_count, name="csv_child_count"),
    url(r"^remindmi", remindmi.malawi_reports, name="remindmi_reports"),
    (r'^', include('rapidsms_xforms.urls')),  # needs top level formList url
    (r'^growth/', include('mwana.apps.nutrition.urls')),
)
