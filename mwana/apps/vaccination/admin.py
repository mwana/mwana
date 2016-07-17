# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.vaccination.models import Client
from mwana.apps.vaccination.models import SentReminders
from mwana.apps.vaccination.models import Appointment
from mwana.apps.vaccination.models import VaccinationSession
from django.contrib import admin

class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_number', 'gender', 'birth_date', 'mother_name', 'mother_age', 'location')
    list_filter = ['gender', 'birth_date', 'location']
    #search_fields = ('client_number', 'gender', 'birth_date', 'mother_name', 'mother_age', 'location')
    date_hierarchy = 'birth_date'
admin.site.register(Client, ClientAdmin)


class VaccinationSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'predecessor', 'min_child_age', 'max_child_age')
    #list_filter = ['session_id', 'predecessor', 'min_child_age', 'max_child_age']
    #search_fields = ('session_id', 'predecessor', 'min_child_age', 'max_child_age')
admin.site.register(VaccinationSession, VaccinationSessionAdmin)


class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'cba_responsible', 'vaccination_session', 'scheduled_date', 'actual_date')
    #list_filter = ['client', 'cba_responsible', 'vaccination_session', 'scheduled_date', 'actual_date']
    #search_fields = ('client', 'cba_responsible', 'vaccination_session', 'scheduled_date', 'actual_date')
    date_hierarchy = 'scheduled_date'
admin.site.register(Appointment, AppointmentAdmin)


class SentRemindersAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'date')
    #list_filter = ['appointment', 'date']
    #search_fields = ('appointment', 'date')
    date_hierarchy = 'date'
admin.site.register(SentReminders, SentRemindersAdmin)
