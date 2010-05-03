from django.contrib import admin
from mwana.apps.labresults.models import *


class ResultAdmin(admin.ModelAdmin):
    list_display = ('sample_id', 'requisition_id', 'clinic', 'clinic_code_unrec',
                    'result', 'collected_on', 'entered_on', 'processed_on',
                    'notification_status',)
    list_filter = ('result', 'collected_on', 'entered_on', 'processed_on', 'clinic', )
admin.site.register(Result, ResultAdmin)

admin.site.register(LabLog)

class PayloadAdmin(admin.ModelAdmin):
    list_display = ('incoming_date', 'auth_user', 'version', 'source',
                    'client_timestamp', 'info', 'parsed_json',
                    'validated_schema')
    list_filter = ('incoming_date', 'auth_user', 'version', 'source',
                   'parsed_json', 'validated_schema')
admin.site.register(Payload, PayloadAdmin)

admin.site.register(LegacyPayload)
