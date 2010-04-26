#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
from mwana.apps.labresults import views


urlpatterns = patterns('',
    url(r"^labresults/$", views.dashboard, name="labresults_dashboard"),
    url(r"^labresults/incoming/$", views.accept_results, name="accept_results"),
        
)
