# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.broadcast.models import BroadcastMessage
from django.contrib import admin

class BroadcastMessageAdmin(admin.ModelAdmin):
    list_display = ( 'contact','location', 'group', 'text', 'logger_message', 'date')
    list_filter = ('group', 'date', 'contact', )
    search_fields = ('contact__name', 'text',
    'contact__location__name',
    'contact__location__parent__name',
    'contact__location__parent__parent__name',
    )
    date_hierarchy = 'date'

    def location(self, obj):
        return obj.contact.location

admin.site.register(BroadcastMessage, BroadcastMessageAdmin)

