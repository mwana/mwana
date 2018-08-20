# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.alerts.models import DhoSMSAlertNotification
from django.contrib import admin
from mwana.apps.alerts.models import Hub
from mwana.apps.alerts.models import Lab
from mwana.apps.alerts.models import SMSAlertLocation

admin.site.register(Hub)

class LabAdmin(admin.ModelAdmin):
    list_display = ('source_key', 'name', 'lab_code', 'phone')
    #list_filter = ['source_key', 'name', 'lab_code', 'phone']
    #search_fields = ('source_key', 'name', 'lab_code', 'phone')
admin.site.register(Lab, LabAdmin)

admin.site.register(SMSAlertLocation)


class DhoSMSAlertNotificationAdmin(admin.ModelAdmin):
    list_display = ('contact', 'district', 'report_type', 'alert_type', 'date_sent')
    list_filter = ('report_type', 'alert_type', 'date_sent', 'district', 'contact',)
    date_hierarchy = 'date_sent'

admin.site.register(DhoSMSAlertNotification, DhoSMSAlertNotificationAdmin)
