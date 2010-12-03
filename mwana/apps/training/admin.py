# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.training import models as training

class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ("start_date", "end_date", "is_on", "trainer", "location", )
    list_filter = ("start_date", "is_on", "location", )
admin.site.register(training.TrainingSession, TrainingSessionAdmin)



