# vim: ai ts=4 sts=4 et sw=4
from rapidsms.models import Contact
from django.contrib import admin

from mwana.apps.reminders import models as reminders


class AppointmentInline(admin.TabularInline):
    model = reminders.Appointment


class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    inlines = (AppointmentInline,)
    list_select_related = True
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug',)
admin.site.register(reminders.Event, EventAdmin)


class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'num_days',)
    list_filter = ('event',)
    list_select_related = True
    search_fields = ('name', 'event__name',)
admin.site.register(reminders.Appointment, AppointmentAdmin)


class PatientEventAdmin(admin.ModelAdmin):
    list_display = ('clinic','patient', 'event', 'date','date_logged','cba',
    'cba_conn','notification_status','notification_sent_date',)
    list_filter = ('event', 'event_location_type', 'date_logged','notification_status',)
    date_hierarchy = 'date_logged'
    search_fields = ('patient__name', 'cba_conn__identity','patient__location__parent__name',)

    def clinic(self, obj):
        try:
            return obj.patient.location.parent.name
        except:
            return "Unknown"
        
    def cba(self, obj):        
        try:
            return Contact.active.filter(connection__identity__icontains=obj.cba_conn.identity)[0].name
        except:
            return "Unknown"
        
admin.site.register(reminders.PatientEvent, PatientEventAdmin)


class SentNotificationInline(admin.TabularInline):
    model = reminders.SentNotification


class SentNotificationAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'patient_event', 'recipient', 'date_logged',)
    list_filter = ('appointment', 'date_logged',)
    list_select_related = True
    search_fields = ('appointment__name', 'patient_event__patient__name', 'recipient__contact__name',
                     'recipient__contact__alias',)
admin.site.register(reminders.SentNotification, SentNotificationAdmin)

