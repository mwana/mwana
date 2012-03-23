# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.tlcprinters import models as tlcprinters


class MessageConfirmationAdmin(admin.ModelAdmin):
    list_display = ('sent_at', 'connection', 'text', 'seq_num', 'confirmed',)
    list_filter = ('sent_at', 'confirmed',)
    search_fields = ('text','connection__identity','connection__contact__name',)
    date_hierarchy = 'sent_at'
    actions = ['mark_confirmed']

    def mark_confirmed(self, request, queryset):
        rows_updated = queryset.update(confirmed=True)
        if rows_updated == 1:
            message_bit = "1 message was"
        else:
            message_bit = "%s messages were" % rows_updated
            self.message_user(request, "%s successfully marked as confirmed." % message_bit)
    mark_confirmed.short_description = "Mark selected messages as confirmed."

admin.site.register(tlcprinters.MessageConfirmation, MessageConfirmationAdmin)
