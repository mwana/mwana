# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.smgl import views


urlpatterns = patterns('',
    url(r"^mothers/$", views.mothers, name="mothers"),
    url(r"^mother/(?P<id>[\d]+)/$", views.mother_history, name="mother-history"),
    url(r"^statistics/$", views.statistics, name="statistics"),
    url(r"^statistics/(?P<id>[\d]+)/$", views.statistics,
            name="district-stats"),
)
