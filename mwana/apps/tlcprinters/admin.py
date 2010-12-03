# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.tlcprinters import models as tlcprinters


class MessageConfirmationAdmin(admin.ModelAdmin):
    list_display = ('sent_at', 'connection', 'text', 'seq_num', 'confirmed',)
    list_filter = ('sent_at', 'confirmed',)
    search_fields = ('connection', 'text')
    date_hierarchy = 'sent_at'
admin.site.register(tlcprinters.MessageConfirmation, MessageConfirmationAdmin)
