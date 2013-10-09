#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns(
    '',
    # contacts export
    url(r'^export$', views.export_contacts, name="export_contacts")
)
