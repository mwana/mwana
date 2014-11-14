from django.conf.urls import patterns, url

from mwana.apps.remindmi import views
# from mwana.apps.appointments import views as app_views

urlpatterns = patterns(
    '',
    url(r'^mothers/$', views.MothersList.as_view(),
        name='mothers_list'),
    url(r'^children/$', views.ChildrenList.as_view(),
        name='children_list'),
    url(r'^mothers/(?P<pk>\d+)/$',
        views.MotherDetailView.as_view(),
        name='mother_detail'),
    url(r'^appointments/$', views.AppointmentList.as_view(),
        name='appointments_list'),
    url(r'^traces/$', views.PatientTraceList.as_view(),
        name='traces_list'),
    url(r'^reminders/$', views.RemindersList.as_view(),
        name='reminders_list'),
    # url(r'^results/$', views.ResultList.as_view(),
        # name='results_list'),
    #  url(r'^children/(?P<pk>\d+)/$',
    # views.ChildDetailView.as_view(),
    # name='child_detail',),
    url(r'^eid/$', views.EIDConfirmationList.as_view(),
        name='eid_list'),
)
