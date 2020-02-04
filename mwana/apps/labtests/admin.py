# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.labtests.models import PreferredBackend
from django.contrib import admin
from mwana.apps.labtests.models import *
from mwana.apps.reports.webreports.actions import export_as_csv_action


def make_obsolete(modeladmin, request, queryset):
    queryset.update(notification_status='obsolete')
make_obsolete.short_description = "Mark selected results as obsolete"


def make_new(modeladmin, request, queryset):
    queryset.update(notification_status='new')
make_new.short_description = "Mark selected results as new"


class ResultAdmin(admin.ModelAdmin):
    list_display = ('sample_id', 'requisition_id', 'clinic', 'clinic_code_unrec',
                    'result', 'collected_on', 'entered_on', 'processed_on',
                    'arrival_date', 'result_sent_date', 'notification_status',
                    'old_value', )
    list_filter = ('processed_on', 'notification_status', 'sex',
                   'collected_on', 'arrival_date', 'result_sent_date', 'clinic',
                   )
    search_fields = ('requisition_id', 'clinic__name', 'clinic__slug', 'result',
                     'phone', 'guspec', )
    date_hierarchy = 'arrival_date'

    actions = [export_as_csv_action(exclude=['id', 'payload']), make_new, make_obsolete]
admin.site.register(Result, ResultAdmin)


class LabLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'message', 'level', 'line', 'source', )
    list_filter = ('timestamp', 'level')
    search_fields = ('message', 'payload__source')

    def source(self, obj):
        return obj.payload.source
        
admin.site.register(LabLog, LabLogAdmin)


class PayloadAdmin(admin.ModelAdmin):
    list_display = ('incoming_date', 'auth_user', 'version', 'source',
                    'client_timestamp', 'info', 'parsed_json',
                    'validated_schema')
    list_filter = ('incoming_date', 'source', 'version',
                   'parsed_json', 'validated_schema', )
    search_fields = ('raw', )

admin.site.register(Payload, PayloadAdmin)


class ViralLoadViewAdmin(admin.ModelAdmin):
    list_display = ('lab_id', 'ptid', 'guspec',  'specimen_collection_date', 'facility_name', 'result', 'date_reached_moh', 'date_facility_retrieved_result', 'who_retrieved', 'date_sms_sent_to_participant', 'data_source', 'author', 'number_of_times_sms_sent_to_participant')
    list_filter = ('test_type', 'data_source', 'specimen_collection_date', 'date_reached_moh', 'date_facility_retrieved_result',
                   'who_retrieved', 'date_sms_sent_to_participant',
                   'facility_name',
                   )
    search_fields = ('guspec', 'specimen_collection_date', 'facility_name', 'result', 'data_source')
    date_hierarchy = 'date_reached_moh'

admin.site.register(ViralLoadView, ViralLoadViewAdmin)


class PreferredBackendAdmin(admin.ModelAdmin):
    list_display = ('phone_first_part', 'backend')
    list_filter = ('backend',)
admin.site.register(PreferredBackend, PreferredBackendAdmin)
