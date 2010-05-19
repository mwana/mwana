from django.contrib import admin
from django import forms
from django.db import models

from mwana.apps.help import models as help


class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('requested_by', 'requested_on', 'additional_text','status',)
    list_filter = ('requested_on',)
    list_select_related = True
    search_fields = ('requested_by', 'status',)
admin.site.register(help.HelpRequest, HelpRequestAdmin)



