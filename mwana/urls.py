# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^my-project/', include('my_project.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin.site.urls)),

    # RapidSMS core URLs
    (r'^accounts/', include('rapidsms.urls.login_logout')),
    url(r'^dashboard$', 'rapidsms.views.dashboard', name='rapidsms-dashboard'),

    # Mwana app URLs
    (r'^labresults/', include('mwana.apps.labresults.urls')),
    (r'^alerts/', include('mwana.apps.alerts.urls')),
    (r'^websms/', include('mwana.apps.websmssender.urls')),
    (r'^export/', include('rapidsms.contrib.export.urls')),
    url(r'^httptester/$',
        'threadless_router.backends.httptester.views.generate_identity',
        {'backend_name': 'httptester'}, name='httptester-index'),
    (r'^httptester/', include('threadless_router.backends.httptester.urls')),
    (r'^backend/', include('threadless_router.backends.kannel.urls')),
    (r'^locations/', include('mwana.apps.locations.urls')),
    (r'^messagelog/', include('rapidsms.contrib.messagelog.urls')),
    (r'^scheduler/', include('scheduler.urls')),
    (r'^locations/', include('mwana.apps.locations.urls')),
    (r'^contacts/', include('mwana.apps.contactsplus.urls')),
    (r'^status/', include('mwana.apps.echo.urls')),
    (r'^smsforms/', include('smsforms.urls')),
    (r'^smscouchforms/', include('smscouchforms.urls')),
    (r'^couchexport/', include('couchexport.urls')),
    (r'^couchforms/', include('couchforms.urls')),
    (r'^couchlog/', include('couchlog.urls')),
    (r'^touchforms/', include('touchforms.urls')),
    (r'^smgl/', include('mwana.apps.smgl.urls')),
)

# Contrib Auth Password Management
urlpatterns += patterns('django.contrib.auth.views',
    url(r'^account/password/change/$', 'password_change', name='auth_password_change'),
    url(r'^account/password/change/done/$', 'password_change_done', name='auth_password_change_done'),
    url(r'^account/password/reset/$', 'password_reset', name='auth_password_reset'),
    url(r'^account/password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'password_reset_confirm',
        name='auth_password_reset_confirm'),
    url(r'^account/password/reset/complete/$', 'password_reset_complete', name='auth_password_reset_complete'),
    url(r'^account/password/reset/done/$', 'password_reset_done', name='auth_password_reset_done'),
)

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^rosetta/', include('rosetta.urls')),
    )

if settings.DEBUG:
    urlpatterns += patterns('',
        # helper URLs file that automatically serves the 'static' folder in
        # INSTALLED_APPS via the Django static media server (NOT for use in
        # production)
        (r'^', include('rapidsms.urls.static_media')),

        (r'^formdesigner/(?P<path>.*)',
         'django.views.static.serve',
         {'document_root': settings.FORMDESIGNER_PATH, 'show_indexes': True}
        ),
    )
