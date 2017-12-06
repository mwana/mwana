# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.act.models import HistoricalEvent
from mwana.apps.act.models import ReminderMessagePreference
from mwana.apps.act.models import SystemUser
from mwana.apps.act.models import RemindersSwitch
from mwana.apps.act.models import VerifiedNumber
from mwana.apps.act.models import CHW
from mwana.apps.act.models import Client
from mwana.apps.act.models import Appointment
from mwana.apps.act.models import SentReminder
from mwana.apps.act.models import ReminderDay
from mwana.apps.act.models import Payload
from django.contrib import admin


class ClientAdmin(admin.ModelAdmin):
    list_display = ('national_id', 'alias', 'dob', 'sex', 'address', 'short_address', 'can_receive_messages', 'location', 'clinic_code_unrec', 'zone', 'phone', 'phone_verified', 'uuid')
    list_filter = ('sex', 'can_receive_messages', 'phone_verified', 'location')
    search_fields = ('national_id', 'alias', 'address', 'short_address',  'location__name', 'phone')
    list_editable = ['can_receive_messages', 'phone_verified']
    date_hierarchy = 'dob'

admin.site.register(Client, ClientAdmin)


class CHAAdmin(admin.ModelAdmin):
    list_display = ('name', 'national_id', 'address', 'location', 'clinic_code_unrec', 'phone', 'phone_verified', 'uuid')
    list_filter = ('phone_verified', 'location', 'clinic_code_unrec')
    search_fields = ('name', 'national_id', 'address', 'location__name', 'location__slug', 'clinic_code_unrec', 'phone', 'phone_verified', 'uuid')
    list_editable = ['phone_verified']
admin.site.register(CHW, CHAAdmin)


class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'cha_responsible', 'type', 'date', 'status', 'notes')
    #list_filter = ('APPOINTMENT_STATUS', 'client', 'cha_responsible', 'type', 'date', 'status', 'notes')
    #search_fields = ('APPOINTMENT_STATUS', 'client', 'cha_responsible', 'type', 'date', 'status', 'notes')
    date_hierarchy = 'date'

admin.site.register(Appointment, AppointmentAdmin)


class ReminderDayAdmin(admin.ModelAdmin):
    list_display = ('appointment_type', 'days')
    #list_filter = ('appointment_type', 'days')
    #search_fields = ('appointment_type', 'days')

admin.site.register(ReminderDay, ReminderDayAdmin)


class SentReminderAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'reminder_type', 'date_logged', 'visit_date')
    list_filter = ('reminder_type', 'date_logged', 'visit_date')
    #search_fields = ('appointment', 'reminder_type', 'date_logged')
    date_hierarchy = 'date_logged'

admin.site.register(SentReminder, SentReminderAdmin)


class PayloadAdmin(admin.ModelAdmin):
    list_display = ('incoming_date', 'auth_user', 'version', 'source',
                    'client_timestamp', 'info', 'parsed_json',
                    'validated_schema')
    list_filter = ('incoming_date',  'source', 'version',
                   'parsed_json', 'validated_schema',)
    search_fields = ('raw',)

admin.site.register(Payload, PayloadAdmin)


class VerifiedNumberAdmin(admin.ModelAdmin):
    list_display = ('number', 'verified')
    list_filter = ('verified',)
    search_fields = ('number',)
    list_editable = ['verified']

admin.site.register(VerifiedNumber, VerifiedNumberAdmin)


class RemindersSwitchAdmin(admin.ModelAdmin):
    list_display = ('logged_on', 'can_send_reminders',  'singleton_lock')
    #list_filter = ('can_send_reminders', 'logged_on', 'singleton_lock')
    #search_fields = ('can_send_reminders', 'logged_on', 'singleton_lock')
    list_editable = ['can_send_reminders']

admin.site.register(RemindersSwitch, RemindersSwitchAdmin)


class SystemUserAdmin(admin.ModelAdmin):
    list_display = ('name', 'password_slice', 'site')
    list_filter = ['site']
    search_fields = ('name',  'site')

admin.site.register(SystemUser, SystemUserAdmin)


class ReminderMessagePreferenceAdmin(admin.ModelAdmin):
    list_display = ('client', 'message_id', 'visit_type')
    list_filter = ['message_id', 'visit_type', 'client',]
    #search_fields = ('client', 'message_id', 'visit_type')
admin.site.register(ReminderMessagePreference, ReminderMessagePreferenceAdmin)


class HistoricalEventAdmin(admin.ModelAdmin):
    list_display = ('date', 'fact_message')
    #list_filter = ['date', 'fact_message']
    search_fields = ('fact_message',)
    date_hierarchy = 'date'
admin.site.register(HistoricalEvent, HistoricalEventAdmin)
