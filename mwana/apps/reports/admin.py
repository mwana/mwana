from django.contrib import admin
from mwana.apps.reports.models import *


class TurnaroundAdmin(admin.ModelAdmin):
    list_display = ('district', 'facility', 'transporting', 'processing',
    'delays','retrieving', 'turnaround', 'date')
    date_hierarchy = 'date'
    list_filter = ('date','district', 'facility')
admin.site.register(Turnaround, TurnaroundAdmin)