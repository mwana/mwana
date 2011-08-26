# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls.defaults import *
from mwana.apps.reports import views

urlpatterns = patterns('',
    # global project URLs:
    (r'^', include('mwana.urls')),
    # custom URL additions for Malawi:
    url(r'^$', views.malawi_reports, name='mwana_reports'),
    (r'^', include('rapidsms_xforms.urls')), # needs top level formList url
    (r'^growth/', include('mwana.apps.nutrition.urls')),
)
