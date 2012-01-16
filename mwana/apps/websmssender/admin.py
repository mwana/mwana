# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.websmssender.models import StagedMessage
from django.contrib import admin
from mwana.apps.websmssender.models import WebSMSLog, StagedMessage

class WebSMSLogAdmin(admin.ModelAdmin):
    list_display = ("date_sent", "sender", "message", "workertype", "location",
                    "recipients_count")
    date_hierarchy = 'date_sent'
    list_filter = ('sender', 'location', 'workertype')
admin.site.register(WebSMSLog, WebSMSLogAdmin)

class StagedMessageAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "text", "connection")
    date_hierarchy = 'date'
    search_fields = ('text',)
admin.site.register(StagedMessage, StagedMessageAdmin)
