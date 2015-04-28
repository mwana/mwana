# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls import patterns, url, include
from mwana.apps.reports import views
from mwana.apps.reminders import views as remindmi
from mwana.apps.labresults import views as results
from mwana.apps.help import views as help
from mwana.apps.emergency import views as emergency
from mwana.apps.dhis2 import views as dhis2
from mwana.apps.nutrition import views as anthro
from rapidsms.backends.http.views import GenericHttpBackendView
from rapidsms.backends.kannel.views import KannelBackendView
from mwana.apps.remindmi.views import ContactsList, send_message
from mwana.apps.monitor.views import MonitorSampleList, result_delivery_stats

urlpatterns = patterns(
    '',
    # Backend urls
    url(r"^backend/zain/$",
        KannelBackendView.as_view(backend_name="zain")),
    url(r"^backend/airtelsmpp/$",
        KannelBackendView.as_view(backend_name="airtelsmpp")),
    url(r"^backend/tnm/$",
        KannelBackendView.as_view(backend_name="tnm")),
    url(r'^backend/httptester/$',
        GenericHttpBackendView.as_view(backend_name='httptester')),
    # url(r'^kannel/', include('rapidsms.backends.kannel.urls')),
    # global project URLs:
    (r'^', include('mwana.urls')),
    # custom URL additions for Malawi:
    url(r'^$', views.dashboard_malawi, name='malawi_home'),
    url(r'^results160/results/', results.ResultList.as_view(),
        name='results_list'),
    url(r'^results160/graphs/', views.malawi_graphs, name='mwana_graphs'),
    url(r'^results160', views.malawi_reports, name='mwana_reports'),
    url(r"^csv/report-one/", views.csv_report_one, name="csv_report_one"),
    url(r"^csv/report-two/", views.csv_report_two, name="csv_report_two"),
    url(r"^csv/mother-count/", remindmi.csv_mother_count,
        name="csv_mother_count"),
    url(r"^csv/child-count/", remindmi.csv_child_count,
        name="csv_child_count"),
    url(r"^remindmi", remindmi.malawi_reports, name="remindmi_reports"),
    (r'^growth/', include('mwana.apps.nutrition.urls')),
    (r'^follow/', include('mwana.apps.remindmi.urls')),
    (r'^appointments/', include('mwana.apps.appointments.urls')),
    url(r'^messages/help/', help.HelpRequestList.as_view(),
        name='help_request_list'),
    url(r'^dhis2/submissions/', dhis2.SubmissionList.as_view(),
        name='dhis2_submission_list'),
    url(r'^anthrowatch/assessments/', anthro.AssessmentReportList.as_view(),
        name='assessment_report_list'),
    url(r'^anthrowatch/graphs/', anthro.report_graphs,
        name='anthro_report_graphs'),
    url(r'^emergency/contacts/send/', send_message,
        name='send_contacts_message'),
    url(r'^emergency/contacts/', ContactsList.as_view(),
        name='emergency_contacts'),
    url(r'^emergency/reports/', emergency.FloodReportList.as_view(),
        name='emergency_flood_list'),
    url(r'^monitor/samples/', MonitorSampleList.as_view(),
        name='monitor_sample_list'),
    url(r'^monitor/delivery/', result_delivery_stats,
        name='monitor_result_delivery'),
)

