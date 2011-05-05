# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.models import CbaEncouragement
from mwana.apps.reports.models import CbaThanksNotification
from django.contrib import admin
from mwana.apps.reports.models import *
from mwana.apps.reports.models import SupportedLocation


class TurnaroundAdmin(admin.ModelAdmin):
    list_display = ('district', 'facility', 'transporting', 'processing',
                    'delays', 'date_reached_moh', 'retrieving', 'date_retrieved',
                    'turnaround')
    date_hierarchy = 'date_retrieved'
    list_filter = ('date_retrieved', 'district', 'facility')
admin.site.register(Turnaround, TurnaroundAdmin)

class MessageGroupAdmin(admin.ModelAdmin):
    list_display = ('date', 'text', 'direction', 'contact_type',
                    'keyword', 'backend', 'changed_res',
                    'new_results', 'app', 'clinic', 'phone')
    date_hierarchy = 'date'
    list_filter = ('before_pilot','direction', 'contact_type', 'keyword', 'backend',
                   'new_results', 'changed_res','clinic', 'phone')
    search_fields = ('text', )
admin.site.register(MessageGroup, MessageGroupAdmin)
#admin.site.register(MessageGroup)

class SupportedLocationAdmin(admin.ModelAdmin):
    list_display = ('location', 'supported')
admin.site.register(SupportedLocation, SupportedLocationAdmin)

class PhoReportNotificationAdmin(admin.ModelAdmin):
    list_display = ('contact', 'province', 'type', 'samples', 'results', 'births', 'date', 'date_sent')
    list_filter = ('province', 'date', 'date_sent')
    date_hierarchy = 'date_sent'
admin.site.register(PhoReportNotification, PhoReportNotificationAdmin)

class DhoReportNotificationAdmin(admin.ModelAdmin):
    list_display = ('contact', 'district', 'type', 'samples', 'results', 'births', 'date', 'date_sent')
    list_filter = ('district', 'date', 'date_sent')
    date_hierarchy = 'date_sent'
admin.site.register(DhoReportNotification, DhoReportNotificationAdmin)

class CbaThanksNotificationAdmin(admin.ModelAdmin):
    list_display = ('contact', 'facility', 'births', 'date', 'date_sent')
    list_filter = ('facility', 'date', 'date_sent')
    date_hierarchy = 'date_sent'
    search_fields = ('contact__name', )
admin.site.register(CbaThanksNotification, CbaThanksNotificationAdmin)

class CbaEncouragementAdmin(admin.ModelAdmin):
    list_display = ('contact', 'facility', 'date_sent')
    list_filter = ('facility', 'date_sent')
    date_hierarchy = 'date_sent'
    search_fields = ('contact__name', )
admin.site.register(CbaEncouragement, CbaEncouragementAdmin)

