# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.reports.webreports.models import GroupFacilityMapping
from mwana.apps.reports.webreports.models import GroupUserMapping
from mwana.apps.reports.webreports.models import ReportingGroup

class GroupFacilityMappingAdmin(admin.ModelAdmin):
    list_display = ('group', 'facility',)
    list_filter = ('group', 'facility',)
    search_fields = ('group__name','facility__name')

admin.site.register(GroupFacilityMapping, GroupFacilityMappingAdmin)

class GroupUserMappingAdmin(admin.ModelAdmin):
    list_display = ('user', 'group',)
    list_filter = ('user', 'group',)
    search_fields = ('group__name','user__username')

admin.site.register(GroupUserMapping, GroupUserMappingAdmin)
admin.site.register(ReportingGroup)

