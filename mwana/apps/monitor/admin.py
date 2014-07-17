# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.monitor.models import Support
from mwana.apps.monitor.models import LostContactsNotification
from mwana.apps.monitor.models import MonitorMessageRecipient
from django.contrib import admin

class MonitorMessageRecipientAdmin(admin.ModelAdmin):
    list_display = ("contact", "receive_sms",)
    list_filter = ("contact", "receive_sms",)
admin.site.register(MonitorMessageRecipient, MonitorMessageRecipientAdmin)


class LostContactsNotificationAdmin(admin.ModelAdmin):
    list_display = ('sent_to', 'facility', 'date')
    list_filter = ('date', 'sent_to', )
    date_hierarchy = 'date'

admin.site.register(LostContactsNotification, LostContactsNotificationAdmin)


from django.contrib import admin

class SupportAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active')
    list_filter = ('user', 'is_active')
    list_editable = ('is_active',)

admin.site.register(Support, SupportAdmin)
