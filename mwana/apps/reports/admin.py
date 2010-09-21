from django.contrib import admin
from mwana.apps.reports.models import *
from mwana.apps.reports.models import SupportedLocation


class TurnaroundAdmin(admin.ModelAdmin):
    list_display = ('district', 'facility', 'transporting', 'processing',
                    'delays', 'date_reached_moh','retrieving', 'date_retrieved',
                    'turnaround')
    date_hierarchy = 'date_retrieved'
    list_filter = ('date_retrieved', 'district', 'facility')
admin.site.register(Turnaround, TurnaroundAdmin)

class SupportedLocationAdmin(admin.ModelAdmin):
    list_display = ('location', 'supported')
admin.site.register(SupportedLocation, SupportedLocationAdmin)