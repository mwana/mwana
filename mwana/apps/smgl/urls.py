# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.smgl import views


urlpatterns = patterns('',
    url(r"^$", views.home_page, name="smgl-home"),
    url(r"^mothers/$", views.mothers, name="mothers"),
    url(r"^mother/(?P<id>[\d]+)/$", views.mother_history, name="mother-history"),
    url(r"^notifications/$", views.notifications, name="notifications"),
    url(r"^referrals/$", views.referrals, name="referrals"),
    url(r"^statistics/$", views.statistics, name="statistics"),
    url(r"^anc-delivery/$", views.anc_delivery_report, name="anc-report"),
    url(r"^pnc-report/$", views.pnc_report, name="pnc-report"),
    url(r"^user-report", views.user_report, name="user-report"),
    url(r"^referral-report/$", views.referral_report, name="referral-report"),
    url(r"^reports-main/$", views.reports_main, name="reports_main"),
    url(r"^statistics/report/$", views.report, name="report"),
    url(r"^statistics/(?P<id>[\d]+)/$", views.statistics,
            name="district-stats"),
    url(r"^statistics/reminder-stats/$", views.reminder_stats, name="reminder-stats"),
    url(r"^sms-records/$", views.sms_records, name="sms-records"),
    url(r"^sms-users/$", views.sms_users, name="sms-users"),
    url(r"^sms-users/(?P<id>[\d]+)/$", views.sms_user_history, name="sms-user-history"),
    url(r"^sms-users/(?P<id>[\d]+)/statistics/$", views.sms_user_statistics, name="sms-user-statistics"),
    url(r"^help/(?P<id>[\d]+)/$", views.help_manager, name="help-manager"),
    url(r"^help/$", views.help, name="help"),
    url(r"^error/$", views.error, name="error_page"),
    url(r"^error-history/(?P<id>[\d]+)$", views.error_history, name="error-history"),
    url(r"^suggestions/$", views.SuggestionList.as_view(), name="suggestions-list"),
    url(r"^suggestion/add/$", views.SuggestionAdd.as_view(), name="suggestions-add"),
    url(r"^suggestion/edit/(?P<pk>[\d]+)/$", views.SuggestionEdit.as_view(), name="suggestions-edit"),
    url(r"^suggestion/detail/(?P<pk>[\d]+)/$", views.SuggestionDetail.as_view(), name="suggestions-detail"),
    url(r"^suggestion/delete/(?P<pk>[\d]+)/$", views.SuggestionDelete.as_view(), name="suggestions-delete"),
)
