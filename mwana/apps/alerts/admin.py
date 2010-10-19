from django.contrib import admin
from mwana.apps.alerts.models import Hub
from mwana.apps.alerts.models import Lab

admin.site.register(Hub)
admin.site.register(Lab)