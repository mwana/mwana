# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.monitor.models import UnrecognisedResult
from django.contrib import admin
from mwana.apps.monitor.models import LostContactsNotification
from mwana.apps.monitor.models import MonitorMessageRecipient
from mwana.apps.monitor.models import Support

class MonitorMessageRecipientAdmin(admin.ModelAdmin):
    list_display = ("contact", "receive_sms", )
    list_filter = ("contact", "receive_sms", )
admin.site.register(MonitorMessageRecipient, MonitorMessageRecipientAdmin)


class LostContactsNotificationAdmin(admin.ModelAdmin):
    list_display = ('sent_to', 'province', 'district', 'facility', 'code', 'date')
    list_filter = ('date', 'sent_to',)
    search_fields = ('facility__name', 'facility__parent__name',
                     'facility__parent__parent__name')
    date_hierarchy = 'date'

    def province(self, obj):
        return obj.facility.parent.parent

    def district(self, obj):
        return obj.facility.parent

    def code(self, obj):
        return obj.facility.slug

admin.site.register(LostContactsNotification, LostContactsNotificationAdmin)


class SupportAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active')
    list_filter = ('user', 'is_active')
    list_editable = ('is_active', )

admin.site.register(Support, SupportAdmin)


class UnrecognisedResultAdmin(admin.ModelAdmin):
    list_display = ('clinic_code_unrec', 'intended_clinic')
    #list_filter = ['clinic_code_unrec', 'intended_clinic']
    search_fields = ('clinic_code_unrec', 'intended_clinic__slug', 'intended_clinic__name')
admin.site.register(UnrecognisedResult, UnrecognisedResultAdmin)
