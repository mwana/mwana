"""Test URL configuration."""

from __future__ import unicode_literals

from django.conf.urls import include, patterns


urlpatterns = patterns('',
    (r'^', include('appointments.urls')),
    (r'^', include('rapidsms.urls.login_logout')),
)
