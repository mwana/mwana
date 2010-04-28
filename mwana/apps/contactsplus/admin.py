from django.contrib import admin

from rapidsms.models import Contact
from rapidsms.admin import ContactAdmin

from mwana.apps.contactsplus import models as contactsplus

admin.site.unregister(Contact)
class ContactAdmin(ContactAdmin):
    list_display = ('unicode', 'alias', 'language', 'location', 'types_list',
                    'is_active',)
    list_filter = ('types', 'is_active', 'language',)
    list_editable = ('is_active',)
    search_fields = ('name', 'alias',)
    
    def unicode(self, obj):
        return unicode(obj)
    
    def types_list(self, obj):
        return ', '.join(obj.types.values_list('name', flat=True))
admin.site.register(Contact, ContactAdmin)


class ContactTypeAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
admin.site.register(contactsplus.ContactType, ContactTypeAdmin)
