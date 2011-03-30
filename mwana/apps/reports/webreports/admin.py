# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.reports.webreports.models import GroupFacilityMapping
from mwana.apps.reports.webreports.models import GroupUserMapping
from mwana.apps.reports.webreports.models import ReportingGroup


admin.site.register(GroupFacilityMapping)
admin.site.register(GroupUserMapping)
admin.site.register(ReportingGroup)

