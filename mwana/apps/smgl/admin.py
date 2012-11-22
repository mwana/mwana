from django.contrib import admin
from .models import *


class XFormKeywordHandlerAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'function_path']


class PreRegsitrationAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'has_confirmed', 'first_name', 'last_name', 'location', 'title', 'language']
    exclude = ['contact', 'has_confirmed']


class PregnantMotherAdmin(admin.ModelAdmin):
    list_display = ['uid', 'contact', 'created_date', 'location', 'zone', 'first_name',
                    'last_name', 'lmp', 'edd', 'next_visit', 'reminded']
    list_filter = ['contact', 'location', 'reminded', 'created_date']


class FacilityVisitAdmin(admin.ModelAdmin):
    list_display = ['location', 'mother', 'created_date', 'visit_date', 'next_visit', 'reason_for_visit',
                    'reminded']
    list_filter = ['reminded', 'created_date']


class AmbulanceRequestAdmin(admin.ModelAdmin):
    list_display = ['requested_on', 'from_location', 'receiving_facility', 'mother', 'mother_uid', 'danger_sign']


class AmbulanceResponseAdmin(admin.ModelAdmin):
    list_display = ['ambulance_request', 'mother', 'mother_uid', 'response']


class AmbulanceOutcomeAdmin(admin.ModelAdmin):
    list_display = ['ambulance_request', 'mother', 'mother_uid', 'outcome']


class ReferralAdmin(admin.ModelAdmin):
    list_display = ['date', 'facility', 'from_facility', 'mother', 'mother_uid', 'responded', 'status',
                    'mother_outcome', 'baby_outcome', 'mode_of_delivery', 'reminded']
    list_filter = ['reminded', 'date']


class BirthRegistrationAdmin(admin.ModelAdmin):
    list_display = ['contact', 'date', 'mother', 'gender', 'place', 'complications', 'number']
    list_filter = ['contact', 'date']


class DeathRegistrationAdmin(admin.ModelAdmin):
    list_display = ['contact', 'date', 'unique_id', 'person', 'place']
    list_filter = ['contact', 'date']


class ReminderNotificationAdmin(admin.ModelAdmin):
    list_display = ['mother', 'mother_uid', 'type', 'recipient', 'date']
    list_filter = ['type']


class ToldReminderAdmin(admin.ModelAdmin):
    list_display = ['mother', 'type', '_session_connection', 'date']
    list_filter = ['type']

    def _session_connection(self, obj):
        return obj.session.contact
    _session_connection.short_description = 'Session Connection'
    _session_connection.admin_order_field = 'session__connection'


admin.site.register(XFormKeywordHandler, XFormKeywordHandlerAdmin)
admin.site.register(PreRegistration, PreRegsitrationAdmin)
admin.site.register(PregnantMother, PregnantMotherAdmin)
admin.site.register(FacilityVisit, FacilityVisitAdmin)
admin.site.register(AmbulanceRequest, AmbulanceRequestAdmin)
admin.site.register(AmbulanceResponse, AmbulanceResponseAdmin)
admin.site.register(Referral, ReferralAdmin)
admin.site.register(BirthRegistration, BirthRegistrationAdmin)
admin.site.register(DeathRegistration, DeathRegistrationAdmin)
admin.site.register(ReminderNotification, ReminderNotificationAdmin)
admin.site.register(ToldReminder, ToldReminderAdmin)
admin.site.register(SyphilisTest)
