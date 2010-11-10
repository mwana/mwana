from django.conf.urls.defaults import *
from mwana.apps.echo import views

urlpatterns = patterns('',
    url(r"^$", views.index, name="labresults_dashboard")
    )

