# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.issuetracking import views


urlpatterns = patterns('',
    url(r"^$", views.list_issues, name="issues"),
)
