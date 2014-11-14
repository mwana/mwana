# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.dhis2.models import Server, Indicator, Submission


class IndicatorAdmin(admin.ModelAdmin):
    list_display = ('server', 'name', 'location', 'period')
    list_filter = ('server', 'name', 'location', )

admin.site.register(Indicator, IndicatorAdmin)


class ServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'url')
    list_filter = ('name', 'url',)

admin.site.register(Server, ServerAdmin)


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('indicator', 'status', 'date_sent')
    list_filter = ('indicator', 'status',)
    date_hierarchy = 'date_sent'

admin.site.register(Submission, SubmissionAdmin)
