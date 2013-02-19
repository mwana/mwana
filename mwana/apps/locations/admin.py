#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.contrib import admin
from .models import *
from django import forms

class LocationAdminForm(forms.ModelForm):
    class Meta:
        model = Location

    def __init__(self, *args, **kwds):
        super(LocationAdminForm, self).__init__(*args, **kwds)
        self.fields['parent'].queryset = Location.objects.exclude(type__slug='zone').order_by('name')

class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "full_name", "send_live_results",
                    "has_independent_printer")
    list_filter = ("type", "send_live_results", "has_independent_printer")
    list_editable = ("send_live_results", "has_independent_printer")
    search_fields = ("name","parent__name", "slug")
    form = LocationAdminForm

class PointAdmin(admin.ModelAdmin):
    list_display = ("latitude", "longitude", "my_location")
    search_fields = ("latitude", "longitude", "location__name",)

    def my_location(self, obj):        
        return ", ".join(loc.name for loc in obj.location_set.all())


admin.site.register(Point, PointAdmin)
admin.site.register(LocationType)
admin.site.register(Location, LocationAdmin)
