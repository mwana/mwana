# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.labtests.models import *


def make_obsolete(modeladmin, request, queryset):
    queryset.update(notification_status='obsolete')
make_obsolete.short_description = "Mark selected results as obsolete"


def make_new(modeladmin, request, queryset):
    queryset.update(notification_status='new')
make_new.short_description = "Mark selected results as new"


class ResultAdmin(admin.ModelAdmin):
    list_display = ('requisition_id', 'payload', 'clinic', 'clinic_code_unrec',
                    'result', 'result_unit', 'processed_on', 'notification_status', 'sex',
                    'result_sent_date', 'phone', 'guspec', 'province', 'district', 'constit',
                    'ward', 'csa', 'sea')
    list_filter = ('processed_on', 'notification_status', 'sex',
                   'result_sent_date', 'phone', 'guspec', 'province', 'district', 'clinic',
                   'constit', 'ward', 'csa', 'sea')
    search_fields = ('requisition_id', 'clinic__name', 'clinic__slug', 'result',
                     'phone', 'guspec', )
    date_hierarchy = 'result_sent_date'

    actions = [make_new, make_obsolete]
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
