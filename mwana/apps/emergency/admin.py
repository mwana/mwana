# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin

from mwana.apps.emergency import models as emergency
from mwana.apps.labresults.actions import export_as_csv_action


class FloodReportAdmin(admin.ModelAdmin):
    list_display = ('parent_loc', 'location', 'reported_by', 'name', 'type',
                    'reported_on', 'additional_text', 'status',)
    list_filter = ('reported_on', 'status',)
    list_select_related = True
    search_fields = ('reported_by__identity', 'status',
                     'reported_by__contact__name', 'additional_text',
                     'reported_by__contact__location__parent__name',
                     'reported_by__contact__types__name',)
    actions = [export_as_csv_action("Export selected reports to CSV.")]

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'resolved_by', None) is None:
            obj.resolved_by = request.user
        obj.save()

    def type(self, obj):
        try:
            return ",".join(
                type.name for type in obj.reported_by.contact.types.all())
        except:
            return ""

    def parent_loc(self, obj):
        try:
            return obj.reported_by.contact.location.parent.name
        except:
            return "Unknown"

    def location(self, obj):
        try:
            return obj.reported_by.contact.location.name
        except:
            return "Unknown"

    def name(self, obj):
        try:
            return obj.reported_by.contact.name
        except:
            return ""

admin.site.register(emergency.FloodReport, FloodReportAdmin)
