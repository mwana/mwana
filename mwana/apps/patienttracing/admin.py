from django.contrib import admin
from mwana.apps.patienttracing.models import PatientTrace

class PatientTraceAdmin(admin.ModelAdmin):
    list_display = ('name', 'patient', 'cba', 'status', 'start_date', 'sent_date'
                    , 'confirmed_date',)
    list_filter = ('cba', 'start_date', 'sent_date', 'confirmed_date')
    search_fields = ('name', 'cba',)
    date_hierarchy = 'confirmed_date'
admin.site.register(PatientTrace, PatientTraceAdmin)

