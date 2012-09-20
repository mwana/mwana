# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.patienttracing.models import PatientTrace

class PatientTraceAdmin(admin.ModelAdmin):
    list_display = ('name', 'patient_event', 'messenger', 'confirmed_by', 'status', 'start_date',
                     'confirmed_date',)
    list_filter = ('status', 'messenger','confirmed_by', 'start_date', 'reminded_date', 'confirmed_date')
    search_fields = ('name', 'messenger','confirmed_by')
    date_hierarchy = 'confirmed_date'
admin.site.register(PatientTrace, PatientTraceAdmin)

