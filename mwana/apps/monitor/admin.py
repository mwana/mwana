# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.monitor.models import MonitorMessageRecipient
from django.contrib import admin

class MonitorMessageRecipientAdmin(admin.ModelAdmin):
    list_display = ("contact", "receive_sms",)
    list_filter = ("contact", "receive_sms",)
admin.site.register(MonitorMessageRecipient, MonitorMessageRecipientAdmin)

