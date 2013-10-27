# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls import patterns, url, include
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^admin/', include(admin.site.urls)),
    # RapidSMS core URLs
    (r'^accounts/', include('rapidsms.urls.login_logout')),
    url(r'^dashboard$', 'rapidsms.views.dashboard', name='rapidsms-dashboard'),
    # Mwana app URLs
    (r'^labresults/', include('mwana.apps.labresults.urls')),
    (r'^alerts/', include('mwana.apps.alerts.urls')),
    (r'^websms/', include('mwana.apps.websmssender.urls')),
    (r'^httptester/', include('rapidsms.contrib.httptester.urls')),
    (r'^locations/', include('mwana.apps.locations.urls')),
    (r'^messagelog/', include('rapidsms.contrib.messagelog.urls')),
    (r'^messaging/', include('rapidsms.contrib.messaging.urls')),
    (r'^locations/', include('mwana.apps.locations.urls')),
    (r'^contacts/', include('mwana.apps.contactsplus.urls')),
    # Third party URLs
    (r'^selectable/', include('selectable.urls')),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
