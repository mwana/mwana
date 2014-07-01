# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.reminders.experimental.models import Supported
from mwana.apps.reminders.experimental.models import SentNotificationToClinic
from django.contrib import admin

class SentNotificationToClinicAdmin(admin.ModelAdmin):
    list_display = ('location', 'event_name', 'number', 'recipients', 'date_logged', 'week')
    list_filter = ('event_name', 'date_logged', 'location',)
    date_hierarchy = 'date_logged'

admin.site.register(SentNotificationToClinic, SentNotificationToClinicAdmin)


class SupportedAdmin(admin.ModelAdmin):
    list_display = ('location', 'supported')
    list_filter = ('location', 'supported')
    list_editable = ('supported',)

admin.site.register(Supported, SupportedAdmin)
