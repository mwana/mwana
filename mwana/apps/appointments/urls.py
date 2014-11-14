from __future__ import unicode_literals

from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns('',
    url(r'^$',
        views.AppointmentList.as_view(),
        name='appointment_list',
    ),
    url(r'^csv/$',
        views.CSVAppointmentList.as_view(),
        name='csv_appointment_list',
    ),
)
