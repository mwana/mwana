#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from django.conf.urls.defaults import *

import views as v


urlpatterns = patterns('',
    # mini dashboard for this app
    #url(r'^$', v.index, name='growth_index'),
    url(r'^$', v.reports, name='growth_index'),
    url(r'^csv/surveyentries/$', v.csv_entries, name='growth_surveyentries'),
    url(r'^csv/assessments/$', v.csv_assessments, name='growth_assessments'),
)