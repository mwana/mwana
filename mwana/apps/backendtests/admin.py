# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.backendtests.models import ForwardedMessage
from django.contrib import admin

class ForwardedMessageAdmin(admin.ModelAdmin):
    list_display = ("connection", "date_sent", "responded", "date_responded", "response",)
    list_filter = ("responded", )
    search_fields = ("text", 'connection__identity',)
admin.site.register(ForwardedMessage, ForwardedMessageAdmin)




