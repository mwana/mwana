# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from django import forms
from django.db import models

from rapidsms.router import send

from mwana.apps.help import models as help
from mwana.apps.labresults.actions import export_as_csv_action


class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('parent_loc', 'location', 'requested_by', 'name', 'type',
                    'requested_on', 'additional_text', 'status',)
    list_filter = ('requested_on', 'status',)
    list_select_related = True
    search_fields = ('requested_by__identity', 'status', 'requested_by__contact__name',
                     'additional_text',
                     'requested_by__contact__location__parent__name',
                     'requested_by__contact__types__name',)
    actions = [export_as_csv_action("Export selected requests to CSV."), 'resend_pin']

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'resolved_by', None) is None:
            obj.resolved_by = request.user
        obj.save()

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


    def resend_pin(self, request, queryset):
        """
        Resend the PIN code to the requesting user. ! After verification of identification
        on phone.
        """
        updated_users = queryset.count()
        for request in queryset:
            pin_code = request.requested_by.contact.pin
            conn = [request.requested_by]
            msg = "Your pin code is %s. Please delete this message after reading." % pin_code
            send(msg, conn)
            request.status = 'R'
            request.notes = 'The pin code was resent to the client.'
            request.save()

        if updated_users == 1:
            message_bit = "1 user was "
        else:
            message_bit = "%s users were " % updated_users
        # self.message_user(request, "%s successfully updated." % message_bit)

    resend_pin.short_description = "Resend pin code to selected requests."

admin.site.register(help.HelpRequest, HelpRequestAdmin)
