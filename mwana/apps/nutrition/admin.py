#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin 
from models import *

class AssessmentInline(admin.TabularInline):
    model = Assessment

class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('status', 'healthworker', 'patient', 'date')
    search_fields = ('healthworker', 'patient', 'date', 'status')
    date_hierarchy = 'date'

class SurveyEntryAdmin(admin.ModelAdmin):
    list_display = ('child_id', 'survey_date')


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('location', 'begin_date', 'end_date')
    seach_fields = ('begin_date', 'end_date', 'location', 'description')

admin.site.register(Assessment, AssessmentAdmin)
admin.site.register(SurveyEntry, SurveyEntryAdmin)
admin.site.register(Survey, SurveyAdmin)
