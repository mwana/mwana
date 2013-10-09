#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns(
    '',
    # mini dashboard for this app
    url(r'^(?:(?P<location_pk>\d+)/)?$',
        views.dashboard,
        name="locations"),

    # list of all messages sent to contacts at this location (or, if a zone,
    # its immediate parent)
    url(r'^(?P<location_pk>\d+)/messages/$',
        views.list_location_messages,
        name="location_messages"),

    # all other locations paths
    url(r'^((?P<location_code>[a-z\-]+)/(?P<location_type_slug>[a-z\-]+)/)+$',
        views.view_location,
        name="view_location"),

    # view all locations of a location_type
    #url(r'^locations/(?P<location_type_slug>[a-z\-]+)$',
    #    views.view_location_type,
    #    name="view_location_type"),

    # view and/or edit a single location
    #url(r'^locations/(?P<location_type_slug>[a-z\-]+)/(?P<location_pk>\d+)$',
    #    views.edit_location,
    #    name="edit_location"),

    # add a location of a defined type (note that
    # there's no url to define a location of an
    # arbitrary type. since location types rarely
    # change, i'm leaving that to the django admin)
    #url(r'^locations/(?P<location_type_slug>[a-z\-]+)/add$',
    #    views.add_location,
    #    name="add_location")
)
