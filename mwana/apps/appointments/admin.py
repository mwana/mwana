from django.contrib import admin

from .models import Timeline, TimelineSubscription, Milestone, Appointment, Notification


class MilestoneAdmin(admin.ModelAdmin):
    list_filter = ('timeline',)
    list_display = ('name', 'timeline', 'offset')

admin.site.register(Timeline)
admin.site.register(TimelineSubscription)
admin.site.register(Milestone,  MilestoneAdmin)
admin.site.register(Appointment)
admin.site.register(Notification)
