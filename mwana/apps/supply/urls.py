
from django.conf.urls.defaults import *
from . import views


urlpatterns = patterns('',
    url(r"^supplies$", views.dashboard, name="supply_dashboard"),
    url(r"^supplies/requests/(?P<request_pk>\d+)$", views.request_details, name="supply_request_details"),
    url(r"^supplies/locations/(?P<location_pk>\d+)$", views.location_details, name="supply_location_details"),
)
