from django.contrib import admin

from rapidsms.models import Contact

from mwana.apps.contactsplus import models as contactsplus


class ContactTypeAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
admin.site.register(contactsplus.ContactType, ContactTypeAdmin)
