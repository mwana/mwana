# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.monitor.models import MonitorMessageRecipient
from mwana.apps.monitor.models import MonitorSample
from django.contrib import admin

class MonitorMessageRecipientAdmin(admin.ModelAdmin):
    list_display = ("contact", "receive_sms",)
    list_filter = ("contact", "receive_sms",)
admin.site.register(MonitorMessageRecipient, MonitorMessageRecipientAdmin)

class MonitorSampleAdmin(admin.ModelAdmin):
    list_display = ('sample_id', 'source', 'hmis', 'status')
    list_filter = ('status', 'hmis')
    # date_hierarchy = 'payload.incoming_date'

    def source(self, obj):
        return obj.payload.source

admin.site.register(MonitorSample, MonitorSampleAdmin)
