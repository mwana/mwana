# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from django import forms
from django.db import models

from mwana.apps.help import models as help


class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('requested_by', 'requested_on', 'additional_text','status',)
    list_filter = ('requested_on',)
    list_select_related = True
    search_fields = ('requested_by', 'status',)
    
    def save_model(self, request, obj, form, change):
        if getattr(obj, 'resolved_by', None) is None:
            obj.resolved_by = request.user
        obj.save()
admin.site.register(help.HelpRequest, HelpRequestAdmin)



