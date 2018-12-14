# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.webreports.models import PayloadAuthorWebUserMapping
from mwana.apps.reports.webreports.models import UserPreference
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


class ReportingGroupAdmin(admin.ModelAdmin):
    list_display = ('name')
    search_fields = ('name',)
admin.site.register(ReportingGroup, ReportingGroupAdmin)


class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'preference_name', 'preference_value', 'extra_preference_value')
    #list_filter = ('user', 'preference_name', 'preference_value', 'extra_preference_value')
    #search_fields = ('user', 'preference_name', 'preference_value', 'extra_preference_value')

admin.site.register(UserPreference, UserPreferenceAdmin)


class PayloadAuthorWebUserMappingAdmin(admin.ModelAdmin):
    list_display = ('author', 'web_user')
    list_filter = ['author', 'web_user']
    search_fields = ('author__author__name', 'web_user__web_user__name')

admin.site.register(PayloadAuthorWebUserMapping, PayloadAuthorWebUserMappingAdmin)

