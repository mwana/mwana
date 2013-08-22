# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.patienttracing.models import CorrectedTrace
from django.contrib import admin
from mwana.apps.patienttracing.models import PatientTrace

class PatientTraceAdmin(admin.ModelAdmin):
    list_display = ('name', 'patient_event', 'clinic', 'type', 'messenger', 'confirmed_by', 'status', 'start_date', 'reminded_date',
                     'confirmed_date','initiator',)
    list_filter = ('type', 'status', 'initiator', 'messenger','confirmed_by', 'start_date', 'reminded_date', 'confirmed_date')
    search_fields = ('name', 'messenger__name','confirmed_by__name')
    date_hierarchy = 'confirmed_date'
admin.site.register(PatientTrace, PatientTraceAdmin)

class CorrectedTracesAdmin(admin.ModelAdmin):
    list_display = ('copied_to', 'copied_from', 'copied_to_start_date',
    'copied_from_start_date', 'copied_to_told_date', 'copied_from_told_date','time_difference')
    search_fields = ('copied_from__patient_event__patient__name', 'copied_to__patient_event__patient__name')

    def copied_from_start_date(self, obj):
        return obj.copied_from.start_date.date()

    def copied_to_start_date(self, obj):
        return obj.copied_to.start_date.date()

    def copied_from_told_date(self, obj):
        return obj.copied_from.reminded_date.date()

    def copied_to_told_date(self, obj):
        return obj.copied_to.reminded_date.date()

    def time_difference(self, obj):
        return obj.copied_from.start_date - obj.copied_to.start_date

admin.site.register(CorrectedTrace, CorrectedTracesAdmin)
