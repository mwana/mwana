# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.smgl import views


urlpatterns = patterns('',
    url(r"^mothers/$", views.mothers, name="mothers"),
    url(r"^mother/(?P<id>[\d]+)/$", views.mother_history, name="mother-history"),
    url(r"^notifications/$", views.notifications, name="notifications"),
    url(r"^referrals/$", views.referrals, name="referrals"),
    url(r"^statistics/$", views.statistics, name="statistics"),
    url(r"^statistics/report/$", views.report, name="report"),
    url(r"^statistics/(?P<id>[\d]+)/$", views.statistics,
            name="district-stats"),
    url(r"^statistics/reminder-stats/$", views.reminder_stats, name="reminder-stats"),
    url(r"^sms-users/$", views.sms_users, name="sms-users"),
    url(r"^sms-users/(?P<name>[\w]+)/$", views.sms_user_history, name="sms-user-history"),
    url(r"^sms-users/(?P<name>[\w]+)/statistics/$", views.sms_user_statistics, name="sms-user-statistics"),
    url(r"^help/(?P<id>[\d]+)/$", views.help_manager, name="help-manager"),
    url(r"^help/$", views.help, name="help"),
)
