from mwana.urls import *

urlpatterns += patterns('',
    (r'^growth/', include('growthmonitoring.urls')),
)
