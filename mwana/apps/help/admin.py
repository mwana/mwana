# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.help.models import HelpAdminGroup
from django.contrib import admin

from mwana.apps.help import models as help


class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('parent_loc', 'location', 'requested_by', 'name', 'pin', 'type',
    'requested_on', 'additional_text','status', 'addressed_on',)
    list_filter = ('requested_on', 'status' )
    list_select_related = True
    search_fields = ('requested_by__identity', 'status', 'requested_by__contact__name',
    'additional_text',
    'requested_by__contact__location__parent__name',
    'requested_by__contact__types__name',)
    list_editable = ['status', 'addressed_on',]

    def pin(self, obj):
        try:
            return obj.requested_by.contact.pin
        except AttributeError:
            return ""

    def type(self, obj):
        try:
            return ",".join(type.name for type in obj.requested_by.contact.types.all())
        except AttributeError:
            return ""

    def parent_loc(self, obj):
        try:
            return obj.requested_by.contact.location.parent.name
        except AttributeError:
            return "Unknown"

    def location(self, obj):
        try:
            return obj.requested_by.contact.location.name
        except AttributeError:
            return "Unknown"

    def name(self, obj):
        try:
            return obj.requested_by.contact.name
        except AttributeError:
            return ""

admin.site.register(help.HelpRequest, HelpRequestAdmin)


class HelpAdminGroupAdmin(admin.ModelAdmin):
    list_display = ('contact', 'group')
    list_filter = ('group', 'group')

admin.site.register(HelpAdminGroup, HelpAdminGroupAdmin)

