# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from mwana.apps.anc.models import SentCHWMessage

from mwana.apps.anc.models import EducationalMessage, SentClientMessage, Client


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


class SentClientMessageAdmin(admin.ModelAdmin):
    list_display = ('client', 'message', 'date')
    list_filter = ['date', 'message']
    search_fields = ('client__connection__identity',)
    date_hierarchy = 'date'
admin.site.register(SentClientMessage, SentClientMessageAdmin)


class SentCHWMessageAdmin(admin.ModelAdmin):
    list_display = ('community_worker', 'message', 'date')
    list_filter = ['date', 'message', 'community_worker',  ]
    search_fields = ('community_worker__name', 'community_worker__connection__identity')
    date_hierarchy = 'date'
admin.site.register(SentCHWMessage, SentCHWMessageAdmin)


class CommunityWorkerAdmin(admin.ModelAdmin):
    list_display = ('name', 'facility', 'connection', 'is_active')
    list_filter = ['is_active', 'facility',]
    search_fields = ('name', 'connection__identity',)
    list_editable = ['is_active']
admin.site.register(CommunityWorker, CommunityWorkerAdmin)

