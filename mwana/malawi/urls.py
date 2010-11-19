from django.conf.urls.defaults import *


urlpatterns = patterns('',
    # global project URLs:
    (r'^', include('mwana.urls')),
    # custom URL additions for Malawi:
    (r'^', include('rapidsms_xforms.urls')), # needs top level formList url
)
