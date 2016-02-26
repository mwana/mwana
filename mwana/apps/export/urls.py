# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from mwana.apps.export import views


urlpatterns = patterns('',
    url(r"^get_turnaround", views.get_turnaround, name="turnaround"),
)
