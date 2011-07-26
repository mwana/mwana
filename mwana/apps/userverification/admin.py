# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.userverification.models import UserVerification
from django.contrib import admin


class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ("facility", "contact", "verification_freq", "request",
    "response",  "responded", "request_date", "response_date",)
    list_filter = ("responded", "facility", )

admin.site.register(UserVerification, UserVerificationAdmin)
