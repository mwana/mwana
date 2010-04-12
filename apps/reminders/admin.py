from django.contrib import admin
from django import forms
from django.db import models

from mwana.apps.reminders import models as reminders


class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
admin.site.register(reminders.Language, LanguageAdmin)


class MessageTranslationInline(admin.TabularInline):
    model = reminders.MessageTranslation
    formfield_overrides = {
        models.CharField: {'widget': forms.Textarea(attrs={'rows': '4'})},
    }


class MessageAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = (MessageTranslationInline,)
admin.site.register(reminders.Message, MessageAdmin)


class MessageTranslationAdmin(admin.ModelAdmin):
    list_display = ('text', 'message', 'language')
    formfield_overrides = {
        models.CharField: {'widget': forms.Textarea},
    }
admin.site.register(reminders.MessageTranslation, MessageTranslationAdmin)
