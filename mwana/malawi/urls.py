# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls.defaults import *


urlpatterns = patterns('',
    # global project URLs:
    (r'^', include('mwana.urls')),
    # custom URL additions for Malawi:
    (r'^', include('rapidsms_xforms.urls')), # needs top level formList url
    (r'^growth/', include('growthmonitoring.urls')),
)
