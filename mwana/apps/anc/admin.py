# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin

from mwana.apps.anc.models import EducationalMessage, SentMessage, Client


class EducationalMessageAdmin(admin.ModelAdmin):
    list_display = ('gestational_age', 'text')
    search_fields = ('gestational_age', 'text')

admin.site.register(EducationalMessage, EducationalMessageAdmin)


class ClientAdmin(admin.ModelAdmin):
    list_display = ('facility', 'connection', 'is_active', 'lmp', 'status', 'date_created', 'gestation_at_subscription')
    #list_filter = ['facility', 'connection', 'is_active', 'lmp', 'status', 'date_created', 'gestation_at_subscription']
    #search_fields = ('facility', 'connection', 'is_active', 'lmp', 'status', 'date_created', 'gestation_at_subscription')
    date_hierarchy = 'date_created'
    #list_editable = ['is_active']

admin.site.register(Client, ClientAdmin)


class SentMessageAdmin(admin.ModelAdmin):
    list_display = ('client', 'message', 'date')
    list_filter = ['date',]
    date_hierarchy = 'date'
    #search_fields = ('client', 'message')

admin.site.register(SentMessage, SentMessageAdmin)

