# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.userverification.models import DeactivatedUser
from mwana.apps.userverification.models import UserVerification
from django.contrib import admin
from django.db.models import Max

from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Contact


class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ("facility", "contact", "is_active", "verification_freq", "request",
    "response",  "responded", "request_date", "response_date",
    'date_of_most_recent_sms',)
    list_filter = ("request_date", "responded", "request", "facility", )
    date_hierarchy = 'request_date'

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


def reactivate(modeladmin, request, queryset):
    for da in  queryset:
        contact = da.contact
        if Contact.active.filter(name=contact.name,
            location=contact.location,
            connection__identity=da.connection.identity):
            continue
        contact.is_active = True
        contact.save()
        conn = da.connection
        conn.contact = contact
        conn.save()
        UserVerification.objects.filter(contact=contact).delete()
    queryset.delete()
reactivate.short_description = "Reactivate selected users"


class DeactivatedUserAdmin(admin.ModelAdmin):
    list_display = ("district", "clinic", "contact", "connection", "deactivation_date",)
    search_fields = ('contact__location__name','contact__name', 'connection__identity')
    actions = [reactivate]

    def clinic(self, obj):
        return obj.contact.clinic

    def district(self, obj):
        return obj.contact.district

admin.site.register(DeactivatedUser, DeactivatedUserAdmin)
