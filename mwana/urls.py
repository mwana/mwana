# vim: ai ts=4 sts=4 et sw=4
from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
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
    # (r'^supplies/', include('mwana.apps.supply.urls')),
    # url(r"^reports/$",
    # mwana.apps.labresults.views.mwana_reports,
    # name="mwana_reports"),
    # url(r'^$',
    # mwana.apps.labresults.views.mwana_reports, name="mwana_reports"),
    (r'^export/', include('rapidsms.contrib.export.urls')),
    url(r'^httptester/$',
        'threadless_router.backends.httptester.views.generate_identity',
        {'backend_name': 'httptester'}, name='httptester-index'),
    (r'^httptester/', include('threadless_router.backends.httptester.urls')),
    (r'^locations/', include('mwana.apps.locations.urls')),
    # (r'^messagelog/', include('rapidsms.contrib.messagelog.urls')),
    # (r'^messaging/', include('rapidsms.contrib.messaging.urls')),
    # (r'^registration/', include('rapidsms.contrib.registration.urls')),
    # (r'^scheduler/', include('rapidsms.contrib.scheduler.urls')),
    (r'^locations/', include('mwana.apps.locations.urls')),
    (r'^contacts/', include('mwana.apps.contactsplus.urls')),
    (r'^status/', include('mwana.apps.echo.urls')),
    (r'^backend/', include('threadless_router.backends.kannel.urls')),
    #Kwabi: quick fix to provide a passsword change form to non admins
    #(r'^changepassword/$', 'nonauth.views.password_change',
    # {'template_name': 'accounts/password_change_form.html'}),

)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        # helper URLs file that automatically serves the 'static' folder in
        # INSTALLED_APPS via the Django static media server (NOT for use in
        # production)
        (r'^', include('rapidsms.urls.static_media')),
    )
