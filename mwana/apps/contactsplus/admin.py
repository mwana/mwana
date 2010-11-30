from django.contrib import admin

from rapidsms.models import Contact
from rapidsms.admin import ContactAdmin

from mwana.apps.contactsplus import models as contactsplus
from views import export_to_csv

admin.site.unregister(Contact)
class ContactAdmin(ContactAdmin):
    list_display = ('unicode', 'alias', 'language', 'parent_location',
                   # 'location', 
		    'default_connection', 'types_list',
                    'is_active',)
    list_filter = ('types', 'is_active', 'language',)
    list_editable = ('is_active',)
    search_fields = ('name', 'alias',)
    actions = [export_to_csv]
    
    def unicode(self, obj):
        return unicode(obj)

    def parent_location(self, obj):
        if obj.location:
            return obj.location.parent

    def types_list(self, obj):
        return ', '.join(obj.types.values_list('name', flat=True))
admin.site.register(Contact, ContactAdmin)


class ContactTypeAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
admin.site.register(contactsplus.ContactType, ContactTypeAdmin)
