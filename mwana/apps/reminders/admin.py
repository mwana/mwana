from django.contrib import admin
from django import forms
from django.db import models

from mwana.apps.reminders import models as reminders


class MessageForm(forms.ModelForm):
    
    class Meta:
        model = reminders.Message
    
    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget = forms.Textarea(attrs={'rows': '5'})


class MessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'text',)
    form = MessageForm
    search_fields = ('name', 'text',)
admin.site.register(reminders.Message, MessageAdmin)


class NotificationInline(admin.TabularInline):
    model = reminders.Notification


class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    inlines = (NotificationInline,)
    list_select_related = True
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug',)
admin.site.register(reminders.Event, EventAdmin)


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'num_days', 'message',)
    list_filter = ('event',)
    list_select_related = True
    search_fields = ('name', 'event__name', 'message__name', 'message__text',)
admin.site.register(reminders.Notification, NotificationAdmin)


class PatientEventInline(admin.TabularInline):
    model = reminders.PatientEvent


class SentNotificationInline(admin.TabularInline):
    model = reminders.SentNotification


class PatientAdmin(admin.ModelAdmin):
    list_display = ('name','location','national_id')
    inlines = (PatientEventInline, SentNotificationInline,)
    search_fields = ('name',)
admin.site.register(reminders.Patient, PatientAdmin)


class SentNotificationAdmin(admin.ModelAdmin):
    list_display = ('notification', 'patient', 'recipient', 'date_logged',)
    list_filter = ('notification', 'date_logged',)
    list_select_related = True
    search_fields = ('notification__name', 'patient__name', 'recipient__name',
                     'recipient__alias',)
admin.site.register(reminders.SentNotification, SentNotificationAdmin)

