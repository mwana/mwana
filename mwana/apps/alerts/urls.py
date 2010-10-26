
from django.conf.urls.defaults import *
from mwana.apps.alerts import views


urlpatterns = patterns('',
    url(r"^alerts/$", views.mwana_alerts, name="mwana_alerts"),
)
