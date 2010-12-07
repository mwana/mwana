# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.hub_workflow.models import HubReportNotification
from mwana.apps.hub_workflow.models import HubSampleNotification

class HubSampleNotificationAdmin(admin.ModelAdmin):
    list_display = ("contact", "lab", "count", "count_in_text", "date", "clinic",)
    list_filter = ("count", "date", "clinic", "contact", "lab",)
admin.site.register(HubSampleNotification, HubSampleNotificationAdmin)

class HubReportNotificationAdmin(admin.ModelAdmin):
    list_display = ("contact", "lab", "type", "samples", "results", "date", "date_sent",)
    list_filter = ("type", "date", "date_sent", "contact", "lab", )
admin.site.register(HubReportNotification, HubReportNotificationAdmin)

