# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.userverification.models import DeactivatedUser
from mwana.apps.userverification.models import UserVerification
from django.contrib import admin
from django.db.models import Max

from rapidsms.contrib.messagelog.models import Message



class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ("facility", "contact", "is_active", "verification_freq", "request",
    "response",  "responded", "request_date", "response_date",
    'date_of_most_recent_sms',)
    list_filter = ("responded", "request", "facility", )

    def is_active(self, obj):
        return "Yes" if obj.contact.is_active else "No"
    
    def date_of_most_recent_sms(self, obj):
        latest = Message.objects.filter(
            contact=obj.contact.id,
            direction='I',
        ).aggregate(date=Max('date'))
        if latest['date']:
            return latest['date'].strftime('%d/%m/%Y %H:%M:%S')
        else:
            return 'None'

admin.site.register(UserVerification, UserVerificationAdmin)

class DeactivatedUserAdmin(admin.ModelAdmin):
    list_display = ("district", "clinic", "contact", "connection", "deactivation_date",)

    def clinic(self, obj):
        return obj.contact.clinic

    def district(self, obj):
        return obj.contact.district

admin.site.register(DeactivatedUser, DeactivatedUserAdmin)
