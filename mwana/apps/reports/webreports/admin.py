# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.reports.webreports.models import GroupFacilityMapping
from mwana.apps.reports.webreports.models import GroupUserMapping
from mwana.apps.reports.webreports.models import ReportingGroup

class GroupFacilityMappingAdmin(admin.ModelAdmin):
    list_display = ('group', 'facility',)
    list_filter = ('group', 'facility',)

admin.site.register(GroupFacilityMapping, GroupFacilityMappingAdmin)
admin.site.register(GroupUserMapping)
admin.site.register(ReportingGroup)

