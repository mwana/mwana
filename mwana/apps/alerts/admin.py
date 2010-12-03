# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.alerts.models import Hub
from mwana.apps.alerts.models import Lab

admin.site.register(Hub)
admin.site.register(Lab)