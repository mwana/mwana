# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.birthcertification.models import SupportedLocation
from mwana.apps.birthcertification.models import CertificateNotification
from mwana.apps.birthcertification.models import RegistrationReminder
from django.contrib import admin
from mwana.apps.birthcertification.models import Agent
from mwana.apps.birthcertification.models import Certification

class CertificationAdmin(admin.ModelAdmin):
    list_display = ('location', 'birth', 'reg_notification_date', 'registration_date',
                    'certificate_sent_to_clinic', 'certificate_notification_date', 
                    'parents_got_certificate', 'certificate_number', 'status',)

    list_filter = ('status', 'reg_notification_date', 'registration_date', 
                    'certificate_sent_to_clinic', 'certificate_notification_date', 
                    'parents_got_certificate',)

    search_fields = ('birth__patient__name', 'birth__patient__location__parent__name',)
    date_hierarchy = 'parents_got_certificate'

    def location(self, obj):
        try:
            return "%s" % obj.birth.patient.location
        except:
            return "Unknown"

admin.site.register(Certification, CertificationAdmin)

class AgentAdmin(admin.ModelAdmin):
    list_display = ('contact', 'is_active', )
    list_filter = ('is_active', )
    list_editable = ('is_active', )
    search_fields = ('contact__name', )
admin.site.register(Agent, AgentAdmin)

class RegistrationReminderAdmin(admin.ModelAdmin):
    list_display = ('certification', 'agent', 'date_sent', )
    list_filter = ('date_sent', )
    search_fields = ('agent__contact__name', 'certification__birth__patient_event__patient__name')

admin.site.register(RegistrationReminder, RegistrationReminderAdmin)


class CertificateNotificationAdmin(admin.ModelAdmin):
    list_display = ('certification', 'agent', 'date_sent', )
    list_filter = ('date_sent', )
    search_fields = ('agent__contact__name', 'certification__birth__patient_event__patient__name')

admin.site.register(CertificateNotification, CertificateNotificationAdmin)


class SupportedLocationAdmin(admin.ModelAdmin):
    list_display = ('location', 'supported')
admin.site.register(SupportedLocation, SupportedLocationAdmin)