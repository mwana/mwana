# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.labresults.models import *
from mwana.apps.labresults.actions import export_as_csv_action


class ResultAdmin(admin.ModelAdmin):
    list_display = ('sample_id', 'requisition_id', 'clinic', 'clinic_code_unrec', 'clinic_care_no',
                    'result', 'collected_on', 'entered_on', 'processed_on',
                    'arrival_date', 'result_sent_date', 'notification_status',
                    'verified',)
    list_filter = ('result', 'notification_status', 'verified', 'payload__source',
                   'result_sent_date', 'collected_on',  'entered_on',
                   'processed_on', 'arrival_date', 'clinic',)
    search_fields = ('sample_id','requisition_id', 'clinic_care_no',)
    date_hierarchy = 'result_sent_date'
    actions = [export_as_csv_action("Export selected results as CSV"), 'mark_as_new']

    def mark_as_new(self, request, queryset):
        rows_updated = queryset.update(notification_status='new')
        if rows_updated == 1:
            message_bit = "1 result was reset"
        else:
            message_bit = "%s results were" % rows_updated
            self.message_user(request, "%s to be sent again." % message_bit)
    mark_as_new.short_description = "Mark selected results as new from lab."


admin.site.register(Result, ResultAdmin)


class LabLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'message', 'level', 'line','source',)
    list_filter = ('timestamp', 'level')
    search_fields = ('message', 'level')

    def source(self, obj):
        return obj.payload.source

admin.site.register(LabLog, LabLogAdmin)


class PayloadAdmin(admin.ModelAdmin):
    list_display = ('incoming_date', 'auth_user', 'version', 'source',
                    'client_timestamp', 'info', 'parsed_json',
                    'validated_schema')
    list_filter = ('incoming_date', 'auth_user', 'version', 'source',
                   'parsed_json', 'validated_schema')
admin.site.register(Payload, PayloadAdmin)

class SampleNotificationAdmin(admin.ModelAdmin):
    list_display =('contact', 'location', 'count', 'count_in_text', 'date')
    list_filter =('contact', 'location', 'count', 'count_in_text', 'date')
    date_hierarchy = 'date'
admin.site.register(SampleNotification, SampleNotificationAdmin)

class PendingPinConnectionsAdmin(admin.ModelAdmin):
    list_display =('connection', 'result', 'timestamp')
    date_hierarchy = 'timestamp'
admin.site.register(PendingPinConnections, PendingPinConnectionsAdmin)

class EIDConfirmationAdmin(admin.ModelAdmin):
    list_display =('contact', 'sample', 'status')
    list_filter =('status', 'action_taken', 'age_in_months')
    # TODO: date_hierachy = 'reported'
admin.site.register(EIDConfirmation, EIDConfirmationAdmin)
