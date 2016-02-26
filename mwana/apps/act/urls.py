# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.act import views


urlpatterns = patterns('',
    url(r"^incoming/$", views.accept_appointments, name="accept_appointments"),
)

