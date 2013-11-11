# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from django.db.models import Min, Max

from rapidsms.models import Contact
from rapidsms.models import Connection
from rapidsms.models import Backend
from rapidsms.admin import ContactAdmin
from rapidsms.contrib.messagelog.models import Message

from mwana.apps.contactsplus import models as contactsplus


admin.site.unregister(Contact)
class ContactAdmin(ContactAdmin):
    list_display = ('unicode', 'alias', 'language', 'parent_location',
                    'location', 
		    'default_connection', 'types_list', 'date_of_first_sms',
                    'date_of_most_recent_sms', 'is_active',)
    list_filter = ('types', 'is_active', 'is_help_admin', 'language', 'location')
    list_editable = ('is_active',)
    search_fields = ('name', 'alias', 'location__name', 'location__parent__name',)

    
    def unicode(self, obj):
        return unicode(obj)

    def parent_location(self, obj):
        if obj.location:
            return obj.location.parent

    def types_list(self, obj):
        return ', '.join(obj.types.values_list('name', flat=True))
    
    def date_of_first_sms(self, obj):
        earliest = Message.objects.filter(
            contact=obj.id,
            direction='I',
        ).aggregate(date=Min('date'))
        if earliest['date']:
            return earliest['date'].strftime('%d/%m/%Y %H:%M:%S')
        else:
            return 'None'

    def date_of_most_recent_sms(self, obj):
        latest = Message.objects.filter(
            contact=obj.id,
            direction='I',
        ).aggregate(date=Max('date'))
        if latest['date']:
            return latest['date'].strftime('%d/%m/%Y %H:%M:%S')
        else:
            return 'None'
admin.site.register(Contact, ContactAdmin)


class ContactTypeAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
admin.site.register(contactsplus.ContactType, ContactTypeAdmin)


admin.site.unregister(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("text", "direction", "who", "date",)
    list_filter = ("direction", "date", "contact",)
    search_fields = ("text",)
admin.site.register(Message, MessageAdmin)


def create_action(backend):
    fun = lambda modeladmin, request, queryset: queryset.update(backend=backend)
    name = "mark_%s" % (backend,)
    return (name, (fun, name, "Set selected connections to %s backend" % (backend,)))


admin.site.unregister(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ("identity", "backend", "contact",)
    list_filter = ("backend", "contact",)
    search_fields = ('identity',)

    def get_actions(self, request):
        return dict(create_action(b) for b in Backend.objects.all())
admin.site.register(Connection, ConnectionAdmin)
