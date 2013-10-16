# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.surveillance.models import Separator
from mwana.apps.surveillance.models import Report
from mwana.apps.surveillance.models import Alias
from mwana.apps.surveillance.models import Incident
from django.contrib import admin

class IncidentAdmin(admin.ModelAdmin):
    list_display = ('name', 'indicator_id', 'abbr', 'type')
    list_filter = ('type', )
    search_fields = ('name', 'indicator_id', 'abbr')
admin.site.register(Incident, IncidentAdmin)


class AliasAdmin(admin.ModelAdmin):
    list_display = ('incident', 'name')
    list_filter = ('incident',)
    search_fields = ('incident__name', 'incident__abbr', 'incident__indicator_id', 'name')
admin.site.register(Alias, AliasAdmin)


class ReportAdmin(admin.ModelAdmin):
    list_display = ('incident', 'value', 'date', 'logged_on', 'reporter', 'year', 'month', 'year', 'location')
    list_filter = ('incident', 'date', 'year', 'month', 'year', 'logged_on', 'reporter', 'location')
    #search_fields = ('incident', 'value', 'date', 'logged_on', 'reporter', , 'year', 'month', 'year', 'location')
    date_hierarchy = 'date'
admin.site.register(Report, ReportAdmin)

admin.site.register(Separator)




