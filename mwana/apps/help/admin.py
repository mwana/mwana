# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from django import forms
from django.db import models

from mwana.apps.help import models as help


class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('parent_loc', 'location', 'requested_by', 'name', 'type',
    'requested_on', 'additional_text','status',)
    list_filter = ('requested_on',)
    list_select_related = True
    search_fields = ('requested_by__identity', 'status', 'requested_by__contact__name',
    'requested_by__contact__location__parent__name',
    'requested_by__contact__location__parent__name',
    'requested_by__contact__types__name',)

    def type(self, obj):
        try:
            return ",".join(type.name for type in obj.requested_by.contact.types.all())
        except:
            return ""

    def parent_loc(self, obj):
        try:
            return obj.requested_by.contact.location.parent.name
        except:
            return "Unknown"

    def location(self, obj):
        try:
            return obj.requested_by.contact.location.name
        except:
            return "Unknown"

    def name(self, obj):
        try:
            return obj.requested_by.contact.name
        except:
            return ""
admin.site.register(help.HelpRequest, HelpRequestAdmin)



