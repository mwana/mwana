from django.contrib import admin
from mwana.apps.labresults.models import *


class ResultAdmin(admin.ModelAdmin):
    list_display = ('sample_id', 'requisition_id', 'clinic', 'clinic_code_unrec',
                    'result', 'collected_on', 'entered_on', 'processed_on',
                    'result_sent_date', 'notification_status',)
    list_filter = ('result', 'notification_status', 'result_sent_date','collected_on',
                   'entered_on', 'processed_on', 'clinic', )
    search_fields = ('sample_id','requisition_id')
    date_hierarchy = 'result_sent_date'
admin.site.register(Result, ResultAdmin)


class LabLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'message', 'level', 'line')
    list_filter = ('timestamp', 'level')
admin.site.register(LabLog, LabLogAdmin)


class PayloadAdmin(admin.ModelAdmin):
    list_display = ('incoming_date', 'auth_user', 'version', 'source',
                    'client_timestamp', 'info', 'parsed_json',
                    'validated_schema')
    list_filter = ('incoming_date', 'auth_user', 'version', 'source',
                   'parsed_json', 'validated_schema')
admin.site.register(Payload, PayloadAdmin)
