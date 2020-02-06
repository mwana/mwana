# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.reports import views


urlpatterns = patterns('',
    url(r"^$", views.zambia_reports, name="mwana_reports"),
    url(r'^save_user_preferences/', views.save_user_preferences, name='save_user_preferences'),
    url(r'^vl/', views.vl_reports, name='mwana_vl_reports'),
)
