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
    
    list_display = ('name', 'text')
    form = MessageForm
admin.site.register(reminders.Message, MessageAdmin)


class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'message')
admin.site.register(reminders.Event, EventAdmin)


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'num_days', 'message')
admin.site.register(reminders.Notification, NotificationAdmin)


class RecipientAdmin(admin.ModelAdmin):
    list_display = ('name', 'shortcut', 'language', 'number')
admin.site.register(reminders.Recipient, RecipientAdmin)
