# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.surveillance.models import MissingIncident
from mwana.apps.surveillance.models import GroupIncident
from mwana.apps.surveillance.models import UserIncident
from mwana.apps.surveillance.models import ImportedReport
from mwana.apps.surveillance.models import Source
from mwana.apps.surveillance.models import AgeGroup
from django.contrib import admin
from mwana.apps.surveillance.models import Alias
from mwana.apps.surveillance.models import Incident
from mwana.apps.surveillance.models import Report
from mwana.apps.surveillance.models import Separator
from django.contrib.admin.views.main import ChangeList
from django.db.models import Sum

class IncidentAdmin(admin.ModelAdmin):
    list_display = ('name', 'indicator_id', 'type', 'abbr')
    list_filter = ('type',)
    search_fields = ('name', 'indicator_id', 'abbr')
admin.site.register(Incident, IncidentAdmin)


class AliasAdmin(admin.ModelAdmin):
    list_display = ('incident', 'name')
    list_filter = ('incident', )
    search_fields = ('incident__name', 'incident__abbr', 'incident__indicator_id', 'name')
admin.site.register(Alias, AliasAdmin)


class ReportTotalAveragesChangeList(ChangeList):
    #provide the list of fields that we need to calculate averages and totals
    fields_to_total = ['value']

    def get_total_values(self, queryset):
        """
        Get the totals
        """
        #basically the total parameter is an empty instance of the given model
        total =  Report()
        total.incident = Incident(name="**Total**")
        for field in self.fields_to_total:
            setattr(total, field, queryset.aggregate(Sum(field)).items()[0][1])
        return total

    def get_results(self, request):
        """
        The model admin gets queryset results from this method
        and then displays it in the template
        """
        super(ReportTotalAveragesChangeList, self).get_results(request)
        #first get the totals from the current changelist
        total = self.get_total_values(self.query_set)
        #small hack. in order to get the objects loaded we need to call for
        #queryset results once so simple len function does it
        len(self.result_list)
        #and finally we add our custom rows to the resulting changelist
        self.result_list._result_cache.append(total)


class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'incident', 'location', 'value', 'date', 'reporter',
                    'week_of_year', 'month', 'year',  'raw_value', 'source')
    list_filter = ('date', 'year', 'month', 'week_of_year', 'incident', 'location', 'reporter')
    search_fields = ('incident__alias__name', 'location__name', 'location__parent__name', 'location__parent__parent__name')
    date_hierarchy = 'date'

    def get_changelist(self, request, **kwargs):
        return ReportTotalAveragesChangeList
    
admin.site.register(Report, ReportAdmin)

class SourceAdmin(admin.ModelAdmin):
    list_display = ('message', 'parsed', 'logged_on')
    list_filter = ('parsed', 'logged_on')
    search_fields = ('message__text',)
    date_hierarchy = 'logged_on'

admin.site.register(Source, SourceAdmin)

admin.site.register(Separator)
admin.site.register(AgeGroup)
class ImportedReportAdmin(admin.ModelAdmin):
    list_display = ('source_message', 'report', 'unparsed')
    #list_filter = ('source_message', 'report', 'unparsed')
    #search_fields = ('source_message', 'report', 'unparsed')

admin.site.register(ImportedReport, ImportedReportAdmin)


class UserIncidentAdmin(admin.ModelAdmin):
    list_display = ('user', 'incident')
    list_filter = ('user', 'incident')
    search_fields = ('user', 'incident')
admin.site.register(UserIncident, UserIncidentAdmin)

class GroupIncidentAdmin(admin.ModelAdmin):
    list_display = ('group', 'incident')
    list_filter = ('group', 'incident')
    search_fields = ('group', 'incident')

admin.site.register(GroupIncident, GroupIncidentAdmin)

class MissingIncidentAdmin(admin.ModelAdmin):
    list_display = ('alias_text', 'incident')
    list_filter = ('incident',)
    list_editable= ('incident',)
    search_fields = ('alias_text',)

admin.site.register(MissingIncident, MissingIncidentAdmin)

