#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.contrib import admin
from .models import *


class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "full_name", "send_live_results",
                    "has_independent_printer")
    list_filter = ("type", "send_live_results", "has_independent_printer")
    search_fields = ("name", "parent__name", "slug")
    actions = ['toggle_live_results']
    list_editable = ("send_live_results", "has_independent_printer")

    def toggle_live_results(self, request, queryset):
        rows_updated = queryset.count()
        for i in queryset:
            if (i.send_live_results):
                i.send_live_results = False
            else:
                i.send_live_results = True
            i.save()
        if rows_updated == 1:
            message_bit = "1 location was"
        else:
            message_bit = "%s locations were" % rows_updated
            self.message_user(request, "%s successfully changed." % message_bit)
    toggle_live_results.short_description = "Toggle send live results for selected locations."


admin.site.register(Point)
admin.site.register(LocationType)
admin.site.register(Location, LocationAdmin)
