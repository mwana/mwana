# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from mwana.apps.training import models as training

class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ("start_date", "end_date", "is_on", "trainer", "location", )
    list_filter = ("start_date", "is_on", "location", )
    date_hierarchy = 'start_date'
admin.site.register(training.TrainingSession, TrainingSessionAdmin)

class TrainedAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "type", "email", "phone", "date", "trained_by", "additional_text",)
    list_filter = ("trained_by", "type", "date", "location", )
    date_hierarchy = 'date'
    search_fields = ('name', "location__name", "email", "phone", "additional_text",)
admin.site.register(training.Trained, TrainedAdmin)


